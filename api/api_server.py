from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import uuid
import sys
import os
import json

# Add parent directory to path to import grader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from grader import grade_submission

app = FastAPI()

# Load existing submissions from file
leaderboard_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "leaderboard.json")
if os.path.exists(leaderboard_file):
    with open(leaderboard_file, "r") as f:
        submissions = json.load(f)
else:
    submissions = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins for deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

class Submission(BaseModel):
    user_id: str
    problem_id: str
    code: str

@app.get("/")
async def root():
    return {"message": "Coding Challenge API is running!"}

@app.post("/submit")
async def submit_code(submission: Submission):
    # locate test_cases/<problem_id>.json
    test_case_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_cases", f"{submission.problem_id}.json")
    if not os.path.exists(test_case_path):
        raise HTTPException(status_code=404, detail="Problem test cases not found")

    with open(test_case_path, "r") as f:
        test_data = json.load(f)

    # grade submission
    result = grade_submission(
        code=submission.code,
        problem_id=submission.problem_id,
        user_id=submission.user_id
    )

    # add to leaderboard
    submission_entry = result["submission_entry"]
    submission_entry["replay_result"] = f"{result['score']}/{result['total']} tests passed"
    submission_entry["timestamp"] = datetime.now().isoformat()

    global submissions
    # update leaderboard (replace if better)
    existing = next((entry for entry in submissions
                     if entry["user_id"] == submission.user_id and entry["problem_id"] == submission.problem_id), None)

    if existing:
        if submission_entry["score"] > existing["score"]:
            submissions = [s for s in submissions if s != existing]
            submissions.append(submission_entry)
    else:
        submissions.append(submission_entry)

    with open(leaderboard_file, "w") as f:
        json.dump(submissions, f, indent=2, default=str)

    return {"grade": result, "leaderboard_entry": submission_entry}


@app.get("/leaderboard")
async def get_leaderboard():
    if not submissions:
        return {"leaderboard": []}

    # Sort by score (descending), then by timestamp (ascending)
    sorted_subs = sorted(submissions, key=lambda x: (-x["score"], x["timestamp"]))

    leaderboard = []
    seen = set()

    for entry in sorted_subs:
        uid = entry["user_id"]
        # Keep only the best/latest score per user
        if uid not in seen:
            leaderboard.append({
                "user_id": uid,
                "score": entry["score"],
                "replay_result": entry["replay_result"],
                "timestamp": entry["timestamp"]
            })
            seen.add(uid)

    return {"leaderboard": leaderboard}

@app.get("/problems")
def list_problems():
    problems = []
    test_cases_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_cases")
    for file in os.listdir(test_cases_dir):
        if file.endswith(".json"):
            try:
                with open(os.path.join(test_cases_dir, file), "r") as f:
                    data = json.load(f)
                if "public_tests" in data or "hidden_tests" in data:
                        problems.append(file.replace(".json", ""))
            except Exception as e:
                continue  # skip invalid JSON files
    return {"problems": problems}

@app.get("/problem/{problem_id}")
def get_problem_details(problem_id: str):
    """Get detailed information about a specific problem"""
    try:
        test_case_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_cases", f"{problem_id}.json")
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

# For Vercel deployment
app = app