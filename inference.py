import os
import json
import urllib.request
from typing import List, Optional
from openai import OpenAI

# ---------------------------------------------------------
# HACKATHON MANDATORY ENV VARS
# ---------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")

if not API_KEY:
    print("Error: HF_TOKEN or OPENAI_API_KEY environment variable not set.")
    exit(1)

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
BASE_URL = "http://127.0.0.1:7860" # Local port for FastAPI

TASK_NAME = "easy" 
BENCHMARK = "compliance-scrubber"
MAX_STEPS = 10

# ---------------------------------------------------------
# HACKATHON MANDATORY LOGGING FORMAT
# ---------------------------------------------------------
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    action_str = json.dumps(action) if isinstance(action, dict) else str(action)
    print(f"[STEP] step={step} action={action_str} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

# ---------------------------------------------------------
# ENVIRONMENT API HELPER
# ---------------------------------------------------------
def send_post(endpoint, data=None):
    """Helper function to send POST requests using the standard library."""
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(url, headers=headers, method='POST')
    
    if data is not None:
        req.data = json.dumps(data).encode('utf-8')
        
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

# ---------------------------------------------------------
# LLM AGENT LOOP
# ---------------------------------------------------------
def run_agent():
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    
    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)
    
    # 1. Reset Environment
    reset_res = send_post("/reset", {"task_level": TASK_NAME})
    observation = reset_res.get("observation", {})
    done = False
    
    system_prompt = (
        "You are a cybersecurity AI. You must respond with ONLY valid JSON representing your next action.\n"
        "Valid action_types: 'ExecuteSQL', 'ReadFile', 'WriteFile', 'ListFiles', 'SubmitTask'.\n"
        "Example output:\n"
        "{\"action_type\": \"ReadFile\", \"action_data\": {\"filepath\": \"/data/user_data.txt\"}}"
    )

    try:
        for step in range(1, MAX_STEPS + 1):
            if done:
                break
                
            steps_taken = step
            
            # --- SAFE NETWORK CALL BLOCK ---
            try:
                # Call OpenAI/Proxy to get the next action
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Current Observation: {json.dumps(observation)}. What is your next action JSON?"}
                    ],
                    temperature=0.0
                )
                
                content = completion.choices[0].message.content
                
                # Strip out markdown formatting if the model hallucinates it
                content = content.replace("```json", "").replace("```", "").strip()
                action_json = json.loads(content)
                
            except Exception as e:
                # If network fails or proxy errors out, don't crash. Just submit task with error info.
                action_json = {
                    "action_type": "SubmitTask", 
                    "action_data": {"reasoning": f"Network or Parsing Error: {str(e)}"}
                }
            # -------------------------------
                
            # Execute action in the environment
            step_res = send_post("/step", action_json)
            
            observation = step_res.get("observation", {})
            reward = step_res.get("reward", 0.0)
            done = step_res.get("done", False)
            error = step_res.get("error", None)
            
            rewards.append(reward)
            
            # Mandatory Step Log
            log_step(step=step, action=action_json, reward=reward, done=done, error=error)
            
            if done:
                # Fetch final score from grader
                grader_res = send_post("/grader", {})
                score = grader_res.get("score", 0.0)
                break
                
    finally:
        success = score >= 0.5 
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    run_agent()