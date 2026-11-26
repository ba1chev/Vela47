# The image every sandbox container runs: the slim Python base plus pytest, so a TEST
# subagent can run the tests it writes. Containers have no route out of their network, so
# anything a subagent's code needs at run time has to be installed here, at build time.
# checkov:skip=CKV_DOCKER_2:The containers only sleep until a command is run in them
# checkov:skip=CKV_DOCKER_3:Known limitation, the local sandbox runs as root (see DOCUMENTATION.md, Known limitations)
FROM python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install "pytest==9.2.0"
