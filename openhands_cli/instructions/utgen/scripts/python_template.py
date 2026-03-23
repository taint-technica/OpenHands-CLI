"""
Keploy Gen bash script template for Python projects.

This script is imported by dev_skills.py to compose the skill content.
All content is compiled and protected by Nuitka.
"""

PYTHON_SCRIPT_TEMPLATE = """\
#!/bin/bash

# Load project .env if present (Langfuse keys, etc.)
if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

export API_KEY="{{API_KEY}}"

# Trace taxonomy for downstream observability (OpenHands + Keploy split)
export OPENHANDS_TRACE_SOURCE="{{TRACE_SOURCE}}"
export OPENHANDS_TRACE_FLOW="{{TRACE_FLOW}}"
export OPENHANDS_PROJECT_NAME="{{PROJECT}}"
export OPENHANDS_TRACE_INVOKER="openhands"
export OPENHANDS_TRACE_ID="$(python3 - <<'PY'
import uuid
print(uuid.uuid4().hex[:32])
PY
)"
export LITELLM_METADATA='{"source":"{{TRACE_SOURCE}}","flow":"{{TRACE_FLOW}}","project":"{{PROJECT}}","invoker":"openhands"}'

# Emit a lightweight Langfuse trace marker for Keploy runs.
# This guarantees `source:keploy` appears in Langfuse trace filters even when
# downstream providers do not forward request metadata as trace tags.
python3 - <<'PY' || true
import base64
import datetime as dt
import json
import os
import urllib.request
import uuid

enabled = os.getenv("LANGFUSE_ENABLED", "").strip().lower() in ("1", "true", "yes")
host = os.getenv("KEPLOY_LANGFUSE_HOST", os.getenv("LANGFUSE_HOST", "")).strip().rstrip("/")
pk = os.getenv("KEPLOY_LANGFUSE_PUBLIC_KEY", os.getenv("LANGFUSE_PUBLIC_KEY", "")).strip()
sk = os.getenv("KEPLOY_LANGFUSE_SECRET_KEY", os.getenv("LANGFUSE_SECRET_KEY", "")).strip()

if enabled and host and pk and sk:
  trace_id = os.getenv("OPENHANDS_TRACE_ID") or uuid.uuid4().hex[:32]
  now = dt.datetime.now(dt.UTC).isoformat()
  project = os.getenv("OPENHANDS_PROJECT_NAME", "unknown")
  source = os.getenv("OPENHANDS_TRACE_SOURCE", "keploy")
  flow = os.getenv("OPENHANDS_TRACE_FLOW", "utgen")
  invoker = os.getenv("OPENHANDS_TRACE_INVOKER", "openhands")

  payload = {
    "batch": [
      {
        "id": str(uuid.uuid4()),
        "timestamp": now,
        "type": "trace-create",
        "body": {
          "id": trace_id,
          "name": "keploy",
          "timestamp": now,
          "sessionId": f"keploy::{os.getcwd()}",
          "tags": [project],
          "metadata": {
            "project": project,
            "source": source,
            "flow": flow,
            "invoker": invoker,
            "origin": "keploy-script",
          },
        },
      }
    ]
  }

  auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
  req = urllib.request.Request(
    f"{host}/api/public/ingestion",
    data=json.dumps(payload).encode(),
    headers={
      "Content-Type": "application/json",
      "Authorization": f"Basic {auth}",
    },
    method="POST",
  )
  with urllib.request.urlopen(req, timeout=10):
    pass
PY

ADDITIONAL_PROMPT=""
[ -f "ARCHITECTURE.md" ] && ADDITIONAL_PROMPT="$(cat ARCHITECTURE.md)"

unset VIRTUAL_ENV
[ -d ".venv" ] && source .venv/bin/activate

export OPENHANDS_COVERAGE_REPORT_PATH="${COVERAGE_REPORT_PATH:-coverage.xml}"

KEPLOY_ARGS=(
  --sourceFilePath="{{SOURCE_FILE_PATH}}"
  --testFilePath="{{TEST_FILE_PATH}}"
  --coverageReportPath="${OPENHANDS_COVERAGE_REPORT_PATH}"
  --coverageFormat="cobertura"
  --testCommand="{{TEST_COMMAND}}"
  --expected-coverage={{EXPECTED_COVERAGE}}
  --maxIterations={{MAX_ITERATIONS}}
  --llm-base-url={{LLM_BASE_URL}}
  --model={{MODEL}}
)
[ -n "$ADDITIONAL_PROMPT" ] && KEPLOY_ARGS+=(--additional-prompt="$ADDITIONAL_PROMPT")

keploy gen "${{KEPLOY_ARGS[@]}}"

# Send actual coverage score to Langfuse after Keploy run.
python3 - <<'PY' || true
import base64
import datetime as dt
import json
import os
import urllib.request
import uuid
import xml.etree.ElementTree as ET

enabled = os.getenv("LANGFUSE_ENABLED", "").strip().lower() in ("1", "true", "yes")
host = os.getenv("KEPLOY_LANGFUSE_HOST", os.getenv("LANGFUSE_HOST", "")).strip().rstrip("/")
pk = os.getenv("KEPLOY_LANGFUSE_PUBLIC_KEY", os.getenv("LANGFUSE_PUBLIC_KEY", "")).strip()
sk = os.getenv("KEPLOY_LANGFUSE_SECRET_KEY", os.getenv("LANGFUSE_SECRET_KEY", "")).strip()
trace_id = os.getenv("OPENHANDS_TRACE_ID", "").strip()
coverage_path = os.getenv("OPENHANDS_COVERAGE_REPORT_PATH", "coverage.xml").strip()

if enabled and host and pk and sk and trace_id and os.path.exists(coverage_path):
  line_rate = None
  root = ET.parse(coverage_path).getroot()

  # Cobertura style: <coverage line-rate="0.91" ...>
  cobertura_rate = root.attrib.get("line-rate")
  if cobertura_rate is not None:
    try:
      line_rate = float(cobertura_rate)
    except ValueError:
      line_rate = None

  # JaCoCo style: <counter type="LINE" missed="x" covered="y"/>
  if line_rate is None:
    line_counter = None
    for counter in root.findall(".//counter"):
      if counter.attrib.get("type") == "LINE":
        line_counter = counter
        break
    if line_counter is not None:
      missed = int(line_counter.attrib.get("missed", "0"))
      covered = int(line_counter.attrib.get("covered", "0"))
      total = missed + covered
      if total > 0:
        line_rate = covered / total

  if line_rate is not None:
    line_rate = max(0.0, min(1.0, float(line_rate)))
    now = dt.datetime.now(dt.UTC).isoformat()
    payload = {
      "batch": [
        {
          "id": str(uuid.uuid4()),
          "timestamp": now,
          "type": "score-create",
          "body": {
            "id": uuid.uuid4().hex[:32],
            "traceId": trace_id,
            "name": "coverage_actual",
            "value": line_rate,
            "comment": f"Actual line coverage: {line_rate * 100:.2f}% ({coverage_path})",
          },
        }
      ]
    }

    auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
    req = urllib.request.Request(
      f"{host}/api/public/ingestion",
      data=json.dumps(payload).encode(),
      headers={
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth}",
      },
      method="POST",
    )
    with urllib.request.urlopen(req, timeout=10):
      pass
PY
"""
