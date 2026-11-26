# The image of the sandbox Lambda function in every AWS environment: the Lambda Python base plus
# pytest, so a TEST subagent can run the tests it writes. The function has no route out of
# its network, so anything a subagent's code needs at run time has to be installed here,
# at build time. Built for arm64, the architecture the function runs on.
# checkov:skip=CKV_DOCKER_2:A Lambda function has no health check
# checkov:skip=CKV_DOCKER_3:Lambda runs the function as its own unprivileged user
FROM public.ecr.aws/lambda/python:3.14@sha256:ada43e932bb0126f892fd935622eaab1199129865d7164ae66a06bcbbd975be0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install "pytest==9.2.0"

COPY handler.py ${LAMBDA_TASK_ROOT}/

CMD ["handler.handler"]
