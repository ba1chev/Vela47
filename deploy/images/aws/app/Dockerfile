# The Vela47 server on AWS, run by ECS on a Graviton (arm64) instance in every AWS environment.
# Built once per release by the delivery workflow from the repository root and pushed to ECR,
# then promoted from dev to staging and prod unchanged. The models are called on Amazon
# Bedrock and commands run in the sandbox Lambda function, both with the IAM role of the task,
# so the image holds no Docker client and the task no Docker socket. It runs as an
# unprivileged user, and uvicorn trusts the forwarded headers of the load balancer, the only
# thing that can reach the task, and gets 100 seconds to finish open streams on a stop.
# checkov:skip=CKV_DOCKER_2:ECS checks the server through the load balancer on /api/health
FROM python:3.15-slim@sha256:63bb298d2b7b88f176f51b5189f54ce6535c997682ea70885d2132f5d473a8a5

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin vela47

WORKDIR /vela47

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY db ./db
COPY app ./app

USER vela47

EXPOSE 8000

CMD ["uvicorn", "app.server.server:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*", "--timeout-graceful-shutdown", "100"]
