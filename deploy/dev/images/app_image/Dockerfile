# The Vela47 server for local development. Built with the repository root as its context.
# The image carries the docker CLI with its compose and buildx plugins, because the server
# brings up the sandbox project itself, through the host's Docker socket mounted at
# /var/run/docker.sock, from the compose project copied in at the path it has in the
# repository. Ollama is not in the image: it runs on the host, where it has the GPU.
FROM docker:29.8.1-cli AS docker_cli

FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

COPY --from=docker_cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker_cli /usr/local/libexec/docker/cli-plugins /usr/local/libexec/docker/cli-plugins

WORKDIR /vela47

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY deploy/dev/images/sandbox_image ./deploy/dev/images/sandbox_image
COPY db ./db
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.server.server:app", "--host", "0.0.0.0", "--port", "8000"]
