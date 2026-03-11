"""
Keploy error handling guide.

Common issues and solutions for Keploy unit test generation.
"""

ERROR_HANDLING_GUIDE = """
## Error Handling

### Common Issues and Solutions

1. **Gen_UnitTest.sh not found**
- Ensure script was created in project root
- Check file permissions: `chmod +x Gen_UnitTest.sh`
- Verify script content is correct

2. **Coverage report not generated**
   - Verify test command is correct
   - Check coverage package is installed
   - Run tests manually to verify

3. **Test file not found**
   - Create test file with basic structure before running keploy gen
   - Follow naming conventions

4. **Low coverage after max iterations**
   - Review generated tests manually
   - Consider increasing max iterations
   - Add specific guidance in `--additional-prompt`

## Important Notes

-ALWAYS use `Gen_UnitTest.sh` as the script filename
- If file exists, UPDATE content (do not create duplicate)
- Always display full command and logs during execution
- Never hide error messages - show complete error output
- Test file naming: `<SourceFile>Test.java` (Java), `test_<file>.py` (Python)
- Ensure API_KEY is set (can be "dummy" for local LLM)
- For Java: always run `mvn clean` before keploy gen
- Replace all `{{PLACEHOLDER}}` values with actual values
- Escape double quotes and newlines in ADDITIONAL_PROMPT
- Make script executable: `chmod +x Gen_UnitTest.sh`
"""
