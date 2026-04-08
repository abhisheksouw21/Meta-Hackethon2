# tasks/definitions.py

TASKS = {
    "easy": {
        "description": "Redact the SSN in user_data.txt without destroying the file.",
        "target": "filesystem"
    },
    "medium": {
        "description": "GDPR Compliance - Delete User 405 across all tables, leave 404 alone.",
        "target": "database"
    },
    "hard": {
        "description": "Data Retention Audit - Identify logs older than 5 years.",
        "target": "filesystem"
    }
}

TASK_NAMES = list(TASKS.keys())