from pydantic import BaseModel, Field
from typing import Union, List, Optional

# ==========================================
# OBSERVATIONS (What the environment returns)
# ==========================================

class SQLResult(BaseModel):
    success: bool
    columns: Optional[List[str]] = None
    rows: Optional[List[List[str]]] = None
    error_message: Optional[str] = None

class FileContent(BaseModel):
    success: bool
    filepath: str
    content: Optional[str] = None
    error_message: Optional[str] = None

class SystemMessage(BaseModel):
    message: str

# The master Observation type
Observation = Union[SQLResult, FileContent, SystemMessage]


# ==========================================
# ACTIONS (What the agent is allowed to do)
# ==========================================

class ExecuteSQL(BaseModel):
    query: str = Field(..., description="The SQL query to execute on the mock database. Tables available: Users, Orders, Support_Tickets.")

class ReadFile(BaseModel):
    filepath: str = Field(..., description="The path to the file you want to read (e.g., /data/logs/user_102.txt).")

class WriteFile(BaseModel):
    filepath: str = Field(..., description="The path to the file you want to write or overwrite.")
    content: str = Field(..., description="The full text content to save into the file. Use this for redactions.")

class ListFiles(BaseModel):
    directory: str = Field(..., description="The directory path to list files from (e.g., /data or /logs).")

class SubmitTask(BaseModel):
    reasoning: str = Field(..., description="Call this action when you have completed the objective. Explain your final steps.")

# The master Action type
Action = Union[ExecuteSQL, ReadFile, WriteFile, ListFiles, SubmitTask]