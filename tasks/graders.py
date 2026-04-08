# tasks/graders.py

def grade_state(task_id: str, db_cursor, filesystem: dict) -> float:
    """Evaluates the final state of the database and filesystem."""
    score = 0.01 

    if task_id == "easy":
        content = filesystem.get("/data/user_data.txt", "")
        if "[REDACTED]" in content and "555-01-9999" not in content:
            score = 0.99 
        elif "555-01-9999" not in content:
            score = 0.5 

    elif task_id == "medium":
        if not db_cursor:
            return 0.01
            
        db_cursor.execute("SELECT COUNT(*) FROM Users WHERE id = 404")
        if db_cursor.fetchone()[0] == 0:
            return 0.01 
            
        db_cursor.execute("SELECT COUNT(*) FROM Users WHERE id = 405")
        if db_cursor.fetchone()[0] == 0: score += 0.33
        
        db_cursor.execute("SELECT COUNT(*) FROM Orders WHERE user_id = 405")
        if db_cursor.fetchone()[0] == 0: score += 0.33
        
        db_cursor.execute("SELECT COUNT(*) FROM Support_Tickets WHERE user_id = 405")
        if db_cursor.fetchone()[0] == 0: score += 0.32

    elif task_id == "hard":
        report = filesystem.get("/violation_report.txt", "")
        if "tx_2018.log" in report: score += 0.49
        if "tx_2019.log" in report: score += 0.49
        if "tx_2024.log" in report: score -= 0.5 
            
    return max(0.01, min(0.99, float(score)))

# Adding this standard signature just in case the framework explicitly searches for it
def grade_action(task_id: str, action: str, signals: dict = None) -> float:
    return 0.5