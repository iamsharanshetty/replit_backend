from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import os
import json
from grader import grade_submission
import logging
logging.basicConfig(level=logging.DEBUG)

# Try to import database functions
try:
    from database import init_db, create_user, verify_user
    DATABASE_AVAILABLE = True
    print("✓ Database module imported successfully")
except ImportError as e:
    DATABASE_AVAILABLE = False
    print(f"⚠ Warning: Database module not available - {e}")
    print("⚠ Authentication will not work. Install dependencies: pip install psycopg2-binary passlib[bcrypt]")

app = FastAPI()

# CRITICAL: Add CORS middleware FIRST, before any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("✓ CORS middleware configured")

# Load existing submissions
leaderboard_file = "leaderboard.json"
if os.path.exists(leaderboard_file):
    with open(leaderboard_file, "r") as f:
        submissions = json.load(f)
else:
    submissions = []

# Initialize database on startup
@app.on_event("startup")
async def startup():
    print("🚀 Starting server...")
    if DATABASE_AVAILABLE:
        try:
            init_db()
            print("✓ Database initialized successfully")
        except Exception as e:
            print(f"✗ Database initialization failed: {e}")
    else:
        print("⚠ Running without database support")

# Models
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

# Routes
@app.get("/")
async def root():
    return {
        "message": "Coding Challenge API is running!",
        "status": "ok",
        "database_available": DATABASE_AVAILABLE
    }

@app.post("/signup")
async def signup(request: SignupRequest):
    """User signup endpoint"""
    print(f"📝 Signup request received for username: {request.username}")
    
    if not DATABASE_AVAILABLE:
        print("✗ Signup failed: Database not available")
        raise HTTPException(
            status_code=503, 
            detail="Database service unavailable. Please install: pip install psycopg2-binary passlib[bcrypt]"
        )
    
    try:
        result = create_user(request.username, request.email, request.password)
        if not result["success"]:
            print(f"✗ Signup failed: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        print(f"✓ Signup successful for user: {request.username}")
        return result
    except Exception as e:
        print(f"✗ Signup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/login")
# async def login(request: LoginRequest):
#     """User login endpoint"""
#     print(f"🔐 Login request received for username: {request.username}")
    
#     if not DATABASE_AVAILABLE:
#         print("✗ Login failed: Database not available")
#         raise HTTPException(
#             status_code=503, 
#             detail="Database service unavailable"
#         )
    
#     try:
#         result = verify_user(request.username, request.password)
#         if not result["success"]:
#             print(f"✗ Login failed: {result['error']}")
#             raise HTTPException(status_code=401, detail=result["error"])
#         print(f"✓ Login successful for user: {request.username}")
#         return result
#     except Exception as e:
#         print(f"✗ Login error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(request: LoginRequest):
    """User login endpoint"""
    print(f"🔐 Login request received for username: {request.username}")
    
    if not DATABASE_AVAILABLE:
        print("✗ Login failed: Database not available")
        raise HTTPException(
            status_code=503, 
            detail="Database service unavailable"
        )
    
    try:
        result = verify_user(request.username, request.password)
        if not result["success"]:
            print(f"✗ Login failed: {result['error']}")
            raise HTTPException(status_code=401, detail=result["error"])
        print(f"✓ Login successful for user: {request.username}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Login exception: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()  # This will show full error details
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/problems")
def list_problems():
    """List all available problems"""
    problems = []
    test_cases_dir = "test_cases"
    
    if not os.path.exists(test_cases_dir):
        return {"problems": []}
    
    for file in os.listdir(test_cases_dir):
        if file.endswith(".json"):
            try:
                with open(os.path.join(test_cases_dir, file), "r") as f:
                    data = json.load(f)
                if "public_tests" in data or "hidden_tests" in data:
                    problems.append(file.replace(".json", ""))
            except Exception:
                continue
    
    return {"problems": problems}

@app.get("/problem/{problem_id}")
def get_problem_details(problem_id: str):
    """Get detailed information about a specific problem"""
    try:
        test_case_path = os.path.join("test_cases", f"{problem_id}.json")
        if not os.path.exists(test_case_path):
            raise HTTPException(status_code=404, detail="Problem not found")
        
        with open(test_case_path, "r") as f:
            problem_data = json.load(f)
        
        return {
            "problem_id": problem_id,
            "public_tests": problem_data.get("public_tests", []),
            "hidden_tests_count": len(problem_data.get("hidden_tests", [])),
            "total_tests": len(problem_data.get("public_tests", [])) + len(problem_data.get("hidden_tests", []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading problem: {str(e)}")

# @app.post("/submit")
# async def submit_code(submission: Submission):
#     """Submit code for grading"""
#     test_case_path = os.path.join("test_cases", f"{submission.problem_id}.json")
#     if not os.path.exists(test_case_path):
#         raise HTTPException(status_code=404, detail="Problem test cases not found")

#     with open(test_case_path, "r") as f:
#         test_data = json.load(f)

#     # Grade submission
#     result = grade_submission(
#         code=submission.code,
#         problem_id=submission.problem_id,
#         user_id=submission.user_id
#     )

#     # Add to leaderboard
#     submission_entry = result["submission_entry"]
#     submission_entry["replay_result"] = f"{result['score']}/{result['total']} tests passed"
#     submission_entry["timestamp"] = datetime.now().isoformat()

#     global submissions
#     # Update leaderboard (replace if better)
#     existing = next((entry for entry in submissions
#                      if entry["user_id"] == submission.user_id and entry["problem_id"] == submission.problem_id), None)

#     if existing:
#         if submission_entry["score"] > existing["score"]:
#             submissions = [s for s in submissions if s != existing]
#             submissions.append(submission_entry)
#     else:
#         submissions.append(submission_entry)

#     with open(leaderboard_file, "w") as f:
#         json.dump(submissions, f, indent=2, default=str)

#     return {"grade": result, "leaderboard_entry": submission_entry}


@app.post("/submit")
async def submit_code(submission: Submission):
    """Submit code for grading"""
    # Check if problem exists
    test_case_path = os.path.join("test_cases", f"{submission.problem_id}.json")
    if not os.path.exists(test_case_path):
        raise HTTPException(status_code=404, detail="Problem test cases not found")

    # Grade the submission
    try:
        result = grade_submission(
            code=submission.code,
            problem_id=submission.problem_id,
            user_id=submission.user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")

    # Prepare submission entry for leaderboard
    submission_entry = {
        "submission_id": result["submission_entry"]["submission_id"],
        "user_id": submission.user_id,
        "problem_id": submission.problem_id,
        "score": result["score"],
        "replay_result": f"{result['score']}/{result['total']} tests passed",
        "timestamp": datetime.now().isoformat(),
        "error_details": result.get("error_details", [])
    }

    # Update leaderboard
    global submissions
    
    # Find existing submission for this user and problem
    existing_index = None
    for i, entry in enumerate(submissions):
        if entry["user_id"] == submission.user_id and entry["problem_id"] == submission.problem_id:
            existing_index = i
            break
    
    # Replace if new score is better, otherwise add new entry
    if existing_index is not None:
        if submission_entry["score"] > submissions[existing_index]["score"]:
            submissions[existing_index] = submission_entry
    else:
        submissions.append(submission_entry)

    # Save to file
    try:
        with open(leaderboard_file, "w") as f:
            json.dump(submissions, f, indent=2, default=str)
    except Exception as e:
        print(f"Warning: Failed to save leaderboard: {e}")

    return {
        "grade": {
            "score": result["score"],
            "total": result["total"],
            "replay_result": result["replay_result"],
            "error_details": result.get("error_details", [])[:3]  # Limit to 3 errors
        },
        "leaderboard_entry": submission_entry
    }

# @app.post("/run")
# async def run_code(request: dict):
#     """Run code without grading"""
#     import subprocess
#     import tempfile
#     import time
    
#     try:
#         problem_id = request.get("problem_id")
#         code = request.get("code")
        
#         # Get first public test case
#         test_case_path = f"test_cases/{problem_id}.json"
#         if os.path.exists(test_case_path):
#             with open(test_case_path, "r") as f:
#                 test_data = json.load(f)
#             test_input = test_data.get("public_tests", [{}])[0].get("input", "")
#         else:
#             test_input = ""
        
#         # Create temporary file
#         with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as tmp:
#             tmp_file = tmp.name
#             tmp.write(code + "\n")
#             tmp.write(f"""
# if __name__ == "__main__":
#     import sys
#     from io import StringIO
    
#     input_data = '''{test_input}'''
#     sys.stdin = StringIO(input_data)
    
#     solve()
# """)
#             tmp.flush()
        
#         start_time = time.time()
#         result = subprocess.run(
#             ["python", tmp_file],
#             capture_output=True,
#             text=True,
#             timeout=5
#         )
#         execution_time = round(time.time() - start_time, 3)
        
#         # Clean up
#         os.unlink(tmp_file)
        
#         if result.returncode != 0:
#             return {
#                 "success": False,
#                 "error": result.stderr,
#                 "execution_time": execution_time
#             }
        
#         return {
#             "success": True,
#             "output": result.stdout,
#             "execution_time": execution_time
#         }
        
#     except subprocess.TimeoutExpired:
#         return {"success": False, "error": "Execution timeout (5 seconds)"}
#     except Exception as e:
#         return {"success": False, "error": str(e)}

@app.post("/run")
async def run_code(request: dict):
    """Run code without grading"""
    import subprocess
    import tempfile
    import time
    
    try:
        problem_id = request.get("problem_id")
        code = request.get("code")
        
        if not problem_id or not code:
            return {"success": False, "error": "Missing problem_id or code"}
        
        # Get first public test case
        test_case_path = os.path.join("test_cases", f"{problem_id}.json")
        test_input = ""
        
        if os.path.exists(test_case_path):
            with open(test_case_path, "r") as f:
                test_data = json.load(f)
            public_tests = test_data.get("public_tests", [])
            if public_tests:
                test_input = public_tests[0].get("input", "")
        
        # Create temporary file
        tmp_file = None
        try:
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
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr or "Runtime error occurred",
                    "execution_time": execution_time
                }
            
            return {
                "success": True,
                "output": result.stdout or "(No output)",
                "execution_time": execution_time,
                "test_input": test_input
            }
            
        finally:
            # Clean up temporary file
            if tmp_file and os.path.exists(tmp_file):
                try:
                    os.unlink(tmp_file)
                except:
                    pass
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Execution timeout (5 seconds)"}
    except Exception as e:
        return {"success": False, "error": f"Execution error: {str(e)}"}

@app.get("/leaderboard")
async def get_leaderboard():
    """Get the leaderboard"""
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
    
    # Sort final leaderboard
    leaderboard.sort(key=lambda x: (-x["score"], x["timestamp"]))
    
    return {"leaderboard": leaderboard}

# if __name__ == "__main__":
#     import uvicorn
#     print("Starting server on http://127.0.0.1:8000")
#     uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)