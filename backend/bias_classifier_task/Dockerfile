FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir boto3 requests

COPY classify_task.py .

CMD ["python", "classify_task.py"]