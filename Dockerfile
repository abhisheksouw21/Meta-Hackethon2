FROM python:3.10-slim

WORKDIR /app

# Copy requirement file and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

# Run the FastAPI server via Uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]