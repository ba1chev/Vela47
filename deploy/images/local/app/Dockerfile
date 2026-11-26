# The Vela47 server for local development. Built with the repository root as its context.
# The image carries the docker CLI with its compose and buildx plugins, because the server
# brings up the sandbox project itself, through the host's Docker socket mounted at
# /var/run/docker.sock, from the compose project copied in at the path it has in the
# repository. Ollama is not in the image: it runs on the host, where it has the GPU.
# checkov:skip=CKV_DOCKER_2:Terraform gives the container its health check (modules/docker_app)
# checkov:skip=CKV_DOCKER_3:The server drives the host's Docker socket, which needs root; local only
FROM docker:29.8.1-cli@sha256:018edbc908e08fcc9dbf029c812c34251e9b4719e6f71ca0e5eae2a987d014ca AS docker_cli

FROM python:3.15-slim@sha256:63bb298d2b7b88f176f51b5189f54ce6535c997682ea70885d2132f5d473a8a5

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

COPY deploy/images/local/sandbox ./deploy/images/local/sandbox
COPY db ./db
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.server.server:app", "--host", "0.0.0.0", "--port", "8000"]
