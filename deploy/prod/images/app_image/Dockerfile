# The Vela47 server in production, run by ECS on a Graviton (arm64) instance. Built by
# Terraform from the repository root and pushed to ECR (see deploy/prod/main.tf). The models
# are called on Amazon Bedrock and commands run in the sandbox Lambda function, both with the
# IAM role of the task, so the image holds no Docker client and the task no Docker socket.
FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /vela47

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY db ./db
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.server.server:app", "--host", "0.0.0.0", "--port", "8000"]
