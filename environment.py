import sqlite3
from typing import Tuple, Dict, Any
from models import (
    Action, Observation, ExecuteSQL, ReadFile, WriteFile, ListFiles, SubmitTask, 
    SQLResult, FileContent, SystemMessage
)

class ComplianceEnv:
    def __init__(self):
        self.db_connection = None
        self.filesystem: Dict[str, str] = {}
        self.current_task = None
        self.step_count = 0
        self.max_steps = 15 # Prevent infinite loops

    def reset(self, task_level: str = "easy") -> Observation:
        """Wipes the environment clean and sets up the fake data for a new episode."""
        self.current_task = task_level
        self.step_count = 0
        
        # 1. Reset the In-Memory Database
        if self.db_connection:
            self.db_connection.close()
        self.db_connection = sqlite3.connect(':memory:')
        self.db_connection.row_factory = sqlite3.Row # Returns dict-like rows
        self._seed_database()

        # 2. Reset the Mock Filesystem
        self._seed_filesystem()

        # Return the initial observation to the agent
        return SystemMessage(
            message=f"Environment initialized. Task level: {task_level}. "
                    "You have access to a SQL database (Tables: Users, Orders, Support_Tickets) "
                    "and a local filesystem."
        )

    def _seed_database(self):
        """Creates tables and inserts mock data for the AI to manipulate."""
        cursor = self.db_connection.cursor()
        
        # Create Tables
        cursor.execute("CREATE TABLE Users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
        cursor.execute("CREATE TABLE Orders (id INTEGER PRIMARY KEY, user_id INTEGER, item TEXT)")
        cursor.execute("CREATE TABLE Support_Tickets (id INTEGER PRIMARY KEY, user_id INTEGER, issue TEXT)")

        # Insert Mock Data (User 405 is the target for the Medium Task)
        cursor.execute("INSERT INTO Users VALUES (404, 'Alice Smith', 'alice@example.com')")
        cursor.execute("INSERT INTO Users VALUES (405, 'Bob Jones', 'bob.delete.me@example.com')") 
        
        cursor.execute("INSERT INTO Orders VALUES (101, 404, 'Laptop')")
        cursor.execute("INSERT INTO Orders VALUES (102, 405, 'Monitor')")
        
        cursor.execute("INSERT INTO Support_Tickets VALUES (501, 404, 'Screen broken')")
        cursor.execute("INSERT INTO Support_Tickets VALUES (502, 405, 'Late delivery')")
        
        self.db_connection.commit()

    def _seed_filesystem(self):
        """Creates fake text files for the AI to read and redact."""
        self.filesystem = {
            "/data/user_data.txt": "Customer Profile:\nName: John Doe\nSSN: 555-01-9999\nStatus: Active",
            "/data/public_holiday_schedule.txt": "No sensitive data here. Just holidays.", # Decoy
            "/logs/tx_2018.log": "Transaction 881: Server error in 2018.",
            "/logs/tx_2019.log": "Transaction 882: DB migration in 2019.", # Extra violation
            "/logs/tx_2024.log": "Transaction 992: Payment processed in 2024."
        }

    def state(self) -> Dict[str, Any]:
        """Returns the internal state (required by OpenEnv spec)."""
        return {
            "task": self.current_task,
            "step_count": self.step_count,
            "filesystem_keys": list(self.filesystem.keys())
        }

    def step(self, action: Action) -> Tuple[Observation, float, bool, Dict]:
        """Executes the agent's action and returns the result, reward, and if the episode is done."""
        self.step_count += 1
        reward = 0.0
        done = False
        info = {}

        # Default observation
        obs = SystemMessage(message="Action not recognized.")

        # --- ACTION ROUTING ---
        if isinstance(action, ExecuteSQL):
            obs = self._handle_sql(action.query)
            
        elif isinstance(action, ReadFile):
            obs = self._handle_read(action.filepath)
            
        elif isinstance(action, WriteFile):
            obs = self._handle_write(action.filepath, action.content)

        elif isinstance(action, ListFiles):
            obs = self._handle_list_files(action.directory)
            
        elif isinstance(action, SubmitTask):
            done = True
            # Call the auto-grader when the AI submits
            reward = float(self._grade_task())
            obs = SystemMessage(message=f"Task submitted. Reasoning: {action.reasoning}. Final Score: {reward}")

        # Force stop if agent takes too long
        if self.step_count >= self.max_steps:
            done = True
            info["reason"] = "max_steps_reached"

        return obs, reward, done, info

    # --- ACTION HANDLERS ---
    def _handle_sql(self, query: str) -> SQLResult:
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query)
            self.db_connection.commit()
            
            if query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                # Get column names
                columns = [description[0] for description in cursor.description] if cursor.description else []
                # Convert rows to list of strings for the AI
                string_rows = [[str(item) for item in row] for row in rows]
                return SQLResult(success=True, columns=columns, rows=string_rows)
            else:
                return SQLResult(success=True, rows=[["Query executed successfully."]])
        except Exception as e:
            return SQLResult(success=False, error_message=str(e))

    def _handle_read(self, filepath: str) -> FileContent:
        if filepath in self.filesystem:
            return FileContent(success=True, filepath=filepath, content=self.filesystem[filepath])
        return FileContent(success=False, filepath=filepath, error_message="File not found.")

    def _handle_write(self, filepath: str, content: str) -> FileContent:
        self.filesystem[filepath] = content
        return FileContent(success=True, filepath=filepath, content="File saved successfully.")

    def _handle_list_files(self, directory: str) -> SystemMessage:
        files = [f for f in self.filesystem.keys() if f.startswith(directory)]
        if not files:
            return SystemMessage(message=f"No files found in directory: {directory}")
        return SystemMessage(message=f"Files found: {', '.join(files)}")

    # --- GRADING LOGIC ---
    def _grade_task(self) -> float:
        """Calculates the score bounded strictly between 0.01 and 0.99."""
        score = 0.01 # Hackathon rule: cannot start at exactly 0.0

        # CRITICAL PREVENT CRASH: If grader is called before reset
        if not self.db_connection:
            self.reset(self.current_task or "easy")

        if self.current_task == "easy":
            # EASY: Redact the SSN in user_data.txt
            content = self.filesystem.get("/data/user_data.txt", "")
            if "[REDACTED]" in content and "555-01-9999" not in content:
                score = 0.99 # Hackathon rule: cannot return exactly 1.0
            elif "555-01-9999" not in content:
                score = 0.5 

        elif self.current_task == "medium":
            # MEDIUM: GDPR Compliance - Delete User 405, but leave User 404 alone
            cursor = self.db_connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM Users WHERE id = 404")
            if cursor.fetchone()[0] == 0:
                return 0.01 # Instant fail: cannot return exactly 0.0
                
            cursor.execute("SELECT COUNT(*) FROM Users WHERE id = 405")
            if cursor.fetchone()[0] == 0: score += 0.33
            
            cursor.execute("SELECT COUNT(*) FROM Orders WHERE user_id = 405")
            if cursor.fetchone()[0] == 0: score += 0.33
            
            cursor.execute("SELECT COUNT(*) FROM Support_Tickets WHERE user_id = 405")
            if cursor.fetchone()[0] == 0: score += 0.32

        elif self.current_task == "hard":
            # HARD: Data Retention Audit (Find logs older than 5 years)
            report = self.filesystem.get("/violation_report.txt", "")
            
            if "tx_2018.log" in report:
                score += 0.49
            if "tx_2019.log" in report:
                score += 0.49
                
            if "tx_2024.log" in report:
                score -= 0.5 # Penalty for false positive
            
        # Hard clamp to ensure it never ever hits 0.0 or 1.0 float limits
        return max(0.01, min(0.99, float(score)))