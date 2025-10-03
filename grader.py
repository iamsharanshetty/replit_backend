import subprocess
import tempfile
import json
import uuid
import os
from datetime import datetime

def grade_submission(code: str, problem_id: str, user_id: str):
    try:
        with open(f"test_cases/{problem_id}.json", "r") as f:
            test_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Test cases for '{problem_id}' not found.")

    all_tests = test_data.get("public_tests", []) + test_data.get("hidden_tests", [])
    total_cases = len(all_tests)
    passed_count = 0
    error_details = []

    for i, case in enumerate(all_tests):
        tmp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as tmp:
                tmp_file = tmp.name
                tmp.write(code + "\n")
                tmp.write("""
if __name__ == "__main__":
    import sys
    from io import StringIO

    input_data = \"\"\"{}\"\"\"
    sys.stdin = StringIO(input_data)

    solve()
""".format(case["input"]))
                tmp.flush()

            try:
                result = subprocess.run(
                    ["python", tmp_file],
                    capture_output=True,
                    text=True,
                    timeout=5  # Increased timeout to 5 seconds
                )
                
                if result.returncode != 0:
                    error_details.append(f"Test {i+1}: Runtime error - {result.stderr.strip()}")
                    continue
                
                user_output = result.stdout.strip()
                expected_output = case["expected_output"].strip()

                # Normalize whitespace for comparison (remove all spaces)
                user_output_normalized = user_output.replace(" ", "")
                expected_output_normalized = expected_output.replace(" ", "")

                if user_output_normalized == expected_output_normalized:
                    passed_count += 1
                else:
                    error_details.append(f"Test {i+1}: Expected '{expected_output}', got '{user_output}'")
                    
            except subprocess.TimeoutExpired:
                error_details.append(f"Test {i+1}: Timeout (exceeded 5 seconds)")
                continue
            except Exception as e:
                error_details.append(f"Test {i+1}: Execution error - {str(e)}")
                continue
                
        finally:
            # Clean up temporary file
            if tmp_file and os.path.exists(tmp_file):
                try:
                    os.unlink(tmp_file)
                except OSError:
                    pass

    replay_result = "passed" if passed_count == total_cases else (
        "partially" if passed_count > 0 else "failed"
    )

    submission_entry = {
        "submission_id": str(uuid.uuid4()),
        "user_id": user_id,
        "problem_id": problem_id,
        "score": passed_count,
        "replay_result": replay_result,
        "timestamp": datetime.utcnow(),
        "error_details": error_details[:3]  # Limit to first 3 errors for brevity
    }

    return {
        "score": passed_count,
        "total": total_cases,
        "replay_result": replay_result,
        "submission_entry": submission_entry,
        "error_details": error_details[:5]  # Return some error details for debugging
    }
