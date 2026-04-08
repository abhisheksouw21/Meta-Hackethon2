# tasks/definitions.py

TASKS = {
    "easy": {
        "description": "Redact the SSN in user_data.txt",
        "ideal_action": "SubmitTask",
        "steps": [
            {
                "observation": "Customer Profile: SSN 555-01-9999 found.",
                "signals": {"status": "unredacted"}
            }
        ]
    },
    "medium": {
        "description": "GDPR Compliance - Delete User 405",
        "ideal_action": "SubmitTask",
        "steps": [
            {
                "observation": "Database query reveals User 405 exists.",
                "signals": {"status": "exists"}
            }
        ]
    },
    "hard": {
        "description": "Data Retention Audit",
        "ideal_action": "SubmitTask",
        "steps": [
            {
                "observation": "System logs show tx_2018.log present.",
                "signals": {"status": "violation"}
            }
        ]
    }
}

TASK_NAMES = list(TASKS.keys())