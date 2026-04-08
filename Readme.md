🛡️ OpenEnv: Compliance Scrubber
A real-world AI simulation environment for data privacy, GDPR compliance, and automated data redaction.

📌 Overview
Compliance Scrubber is a simulated enterprise data environment designed to train and evaluate LLM agents on critical cybersecurity and data privacy tasks. Built following the OpenEnv specification, it provides agents with tool access to an in-memory SQL database and a mock filesystem to locate, redact, and purge sensitive Personally Identifiable Information (PII).

This project was developed for the Meta x Scaler OpenEnv Hackathon. It focuses on high real-world utility, moving beyond toy games to simulate tasks that data compliance officers and DevOps engineers perform daily.

🎯 The Tasks & Grading
The environment features a deterministic auto-grader that evaluates agents across three difficulty tiers, rewarding partial progress and heavily penalizing destructive actions (e.g., dropping incorrect tables).

🟢 Easy (SSN Redaction): The agent must locate a specific user file in the filesystem, read it, and successfully redact a Social Security Number using the exact [REDACTED] tag.

🟡 Medium (GDPR "Right to be Forgotten"): The agent is given a specific User ID and must safely purge all traces of that user across three relational SQL tables (Users, Orders, Support_Tickets) without impacting other users' data.

🔴 Hard (Data Retention Audit): The agent must audit a directory of transaction logs, identify files older than a 5-year retention policy, and compile an accurate violation report. Penalties are applied for false positives.

🛠️ Tech Stack
Backend: Python, FastAPI, Uvicorn

Data Simulation: SQLite3 (In-memory), Python Dictionaries

Agent Interface: Pydantic (Strict Schema Tool Calling)

Baseline AI: OpenAI API (gpt-4o / gpt-4o-mini)

Deployment: Docker, Hugging Face Spaces