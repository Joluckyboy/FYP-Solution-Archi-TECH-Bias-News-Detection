FROM python:3.11-slim

WORKDIR /app

# Step 1: Install boto3 and transformers from PyPI (default index)
RUN pip install --no-cache-dir \
    boto3 \
    transformers

# Step 2: Install PyTorch CPU-only from the PyTorch index separately
# --index-url replaces the default index, so it must be done in its own command
RUN pip install --no-cache-dir \
    torch \
    --index-url https://download.pytorch.org/whl/cpu

COPY classify_task.py .

CMD ["python", "classify_task.py"]