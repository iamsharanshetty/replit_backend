from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from database import init_db, create_user, verify_user
import os

# Initialize database on startup

app = FastAPI()
submissions = []

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup():
    init_db()


class Submission(BaseModel):
    user_id: str
    problem_id: str
    code: str

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str



@app.get("/")
async def root():
    return {"message": "Coding Challenge API is running!", "status": "ok"}


@app.post("/signup")
async def signup(request: SignupRequest):
    """User signup"""
    result = create_user(request.username, request.email, request.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/login")
async def login(request: LoginRequest):
    """User login"""
    result = verify_user(request.username, request.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result

@app.get("/problems")
def list_problems():
    problems = [
        "power-of-two", "three-sum", "binary-search-insert-position", 
        "elimination-game", "find-town-judge", "front-middle-back-queue",
        "insertion-sort-pairs", "longest-common-prefix", "max-path-sum-binary-tree",
        "merge-sort", "merge-two-sorted-lists", "regex-matching", 
        "stack-using-queues", "tiny-url-encoder"
    ]
    return {"problems": problems}

@app.post("/submit")
async def submit_code(submission: Submission):
    global submissions
    
    # Mock grading - gives 5/6 tests passed
    score = 5
    total = 6
    
    submission_entry = {
        "user_id": submission.user_id,
        "problem_id": submission.problem_id,
        "score": score,
        "replay_result": f"{score}/{total} tests passed",
        "timestamp": datetime.now().isoformat()
    }
    
    # Update leaderboard
    existing = next((entry for entry in submissions
                     if entry["user_id"] == submission.user_id and entry["problem_id"] == submission.problem_id), None)
    
    if existing:
        if submission_entry["score"] > existing["score"]:
            submissions = [s for s in submissions if s != existing]
            submissions.append(submission_entry)
    else:
        submissions.append(submission_entry)
    
    result = {
        "score": score,
        "total": total,
        "replay_result": "partially"
    }
    
    return {"grade": result, "leaderboard_entry": submission_entry}


@app.post("/run")
async def run_code(request: dict):
    """Run code without grading - just execute with first public test"""
    import subprocess
    import tempfile
    import os
    import time
    
    try:
        problem_id = request.get("problem_id")
        code = request.get("code")
        
        # Get first public test case
        test_case_path = f"test_cases/{problem_id}.json"
        if os.path.exists(test_case_path):
            with open(test_case_path, "r") as f:
                test_data = json.load(f)
            test_input = test_data.get("public_tests", [{}])[0].get("input", "")
        else:
            test_input = ""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as tmp:
            tmp_file = tmp.name
            tmp.write(code + "\n")
            tmp.write(f"""
if __name__ == "__main__":
    import sys
    from io import StringIO
    
    input_data = '''{test_input}'''
    sys.stdin = StringIO(input_data)
    
    solve()
""")
            tmp.flush()
        
        start_time = time.time()
        result = subprocess.run(
            ["python", tmp_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        execution_time = round(time.time() - start_time, 3)
        
        # Clean up
        os.unlink(tmp_file)
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr,
                "execution_time": execution_time
            }
        
        return {
            "success": True,
            "output": result.stdout,
            "execution_time": execution_time
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Execution timeout (5 seconds)"}
    except Exception as e:
        return {"success": False, "error": str(e)}



@app.get("/leaderboard")
async def get_leaderboard():
    if not submissions:
        return {"leaderboard": []}

    # Group by problem_id
    problems = {}
    for entry in submissions:
        pid = entry.get("problem_id", "unknown")
        if pid not in problems:
            problems[pid] = []
        problems[pid].append(entry)
    
    # For each problem, get best submission per user
    leaderboard = []
    for problem_id, entries in problems.items():
        # Sort by score (desc), then timestamp (asc)
        sorted_entries = sorted(entries, key=lambda x: (-x["score"], x["timestamp"]))
        
        seen_users = set()
        for entry in sorted_entries:
            uid = entry["user_id"]
            if uid not in seen_users:
                leaderboard.append({
                    "user_id": uid,
                    "problem_id": problem_id,
                    "score": entry["score"],
                    "replay_result": entry["replay_result"],
                    "timestamp": entry["timestamp"]
                })
                seen_users.add(uid)
    
    # Sort final leaderboard by score (desc), then timestamp (asc)
    leaderboard.sort(key=lambda x: (-x["score"], x["timestamp"]))
    
    return {"leaderboard": leaderboard}

@app.get("/problem/{problem_id}")
def get_problem_details(problem_id: str):
    return {
        "problem_id": problem_id,
        "public_tests": [
            {"input": "sample input", "expected_output": "sample output"}
        ],
        "hidden_tests_count": 5,
        "total_tests": 6
    }