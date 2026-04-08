from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import subprocess
from environment import ComplianceEnv
from models import Action, ExecuteSQL, ReadFile, WriteFile, ListFiles, SubmitTask

# NEW IMPORT: Pulling the decoupled grader from the tasks module
from tasks.graders import grade_state  

app = FastAPI(title="Compliance Scrubber OpenEnv")
env = ComplianceEnv()

# API Models for requests
class StepRequest(BaseModel):
    action_type: str
    action_data: Dict[str, Any]

class ResetRequest(BaseModel):
    task_level: str = "easy"

@app.get("/")
def health_check():
    """Required by Hugging Face to verify the Space is running."""
    return {"status": "ok"}

@app.post("/reset")
def reset_environment(req: Optional[ResetRequest] = None):
    """Resets the environment. Handles empty requests from the auto-grader."""
    # If the grader sends an empty request, default to "easy"
    level = req.task_level if req else "easy"
    obs = env.reset(level)
    return {"observation": obs.model_dump()}

@app.post("/step")
def step_environment(req: StepRequest):
    """Executes an action in the environment."""
    try:
        if req.action_type == "ExecuteSQL":
            action = ExecuteSQL(**req.action_data)
        elif req.action_type == "ReadFile":
            action = ReadFile(**req.action_data)
        elif req.action_type == "WriteFile":
            action = WriteFile(**req.action_data)
        elif req.action_type == "ListFiles":
            action = ListFiles(**req.action_data)
        elif req.action_type == "SubmitTask":
            action = SubmitTask(**req.action_data)
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
    """Returns the internal state of the environment."""
    return env.state()

@app.get("/tasks")
def get_tasks():
    """Reverted to standard OpenEnv format since YAML is handling validation."""
    return {
        "tasks": ["easy", "medium", "hard"]
    }

@app.post("/grader")
def get_grader_score(req: Optional[Dict[str, Any]] = None):
    """Returns the current grader score using the decoupled logic."""
    # Prevent crash if baseline hits /grader before /reset
    if not env.db_connection:
        env.reset(env.current_task or "easy")
        
    cursor = env.db_connection.cursor() if env.db_connection else None
    score = grade_state(env.current_task, cursor, env.filesystem)
    return {"score": score}

@app.get("/baseline")
def run_baseline_endpoint():
    """Triggers the inference script and returns the scores."""
    try:
        result = subprocess.run(["python", "inference.py"], capture_output=True, text=True, check=True)
        return {"status": "success", "logs": result.stdout}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Baseline failed: {e.stderr}")