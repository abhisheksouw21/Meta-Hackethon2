from fastapi import FastAPI, HTTPException, Request
from typing import Dict, Any, Optional
import subprocess
from environment import ComplianceEnv
from models import Action, ExecuteSQL, ReadFile, WriteFile, ListFiles, SubmitTask
from tasks.graders import grade_state  

app = FastAPI(title="Compliance Scrubber OpenEnv")
env = ComplianceEnv()

@app.get("/")
def health_check():
    """Required by Hugging Face to verify the Space is running."""
    return {"status": "ok"}

@app.post("/reset")
async def reset_environment(request: Request):
    """Bulletproof reset that catches task_id or task_level."""
    try:
        body = await request.json()
    except:
        body = {}
        
    level = body.get("task_id", body.get("task_level", "easy"))
    obs = env.reset(level)
    return {"observation": obs.model_dump()}

@app.post("/step")
async def step_environment(request: Request):
    """Executes an action in the environment."""
    body = await request.json()
    try:
        action_type = body.get("action_type")
        action_data = body.get("action_data", {})
        
        if action_type == "ExecuteSQL":
            action = ExecuteSQL(**action_data)
        elif action_type == "ReadFile":
            action = ReadFile(**action_data)
        elif action_type == "WriteFile":
            action = WriteFile(**action_data)
        elif action_type == "ListFiles":
            action = ListFiles(**action_data)
        elif action_type == "SubmitTask":
            action = SubmitTask(**action_data)
        else:
            raise ValueError("Unknown action_type")
            
        obs, float_reward, done, info = env.step(action)
        return {
            "observation": obs.model_dump(),
            "reward": float_reward,
            "done": done,
            "info": info
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/state")
def get_state():
    return env.state()

@app.get("/tasks")
def get_tasks():
    return {
        "tasks": ["easy", "medium", "hard"],
        "action_schema": "ExecuteSQL(query), ReadFile(filepath), WriteFile(filepath, content), ListFiles(directory), SubmitTask(reasoning)"
    }

@app.post("/grader")
async def get_grader_score(request: Request):
    """Bulletproof grader that checks the specific task the validator asks for."""
    try:
        body = await request.json()
    except:
        body = {}
    
    # Catch whatever key the auto-grader throws at us
    task_id = body.get("task_id", body.get("task_level", env.current_task or "easy"))
    
    # If the grader asks for a task that isn't currently loaded, spin it up instantly
    if not env.db_connection or env.current_task != task_id:
        env.reset(task_id)
        
    cursor = env.db_connection.cursor() if env.db_connection else None
    score = grade_state(task_id, cursor, env.filesystem)
    return {"score": score}

@app.get("/baseline")
def run_baseline_endpoint():
    try:
        result = subprocess.run(["python", "inference.py"], capture_output=True, text=True, check=True)
        return {"status": "success", "logs": result.stdout}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Baseline failed: {e.stderr}")