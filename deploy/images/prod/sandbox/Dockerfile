# The image of the sandbox Lambda function in production: the Lambda Python base plus
# pytest, so a TEST subagent can run the tests it writes. The function has no route out of
# its network, so anything a subagent's code needs at run time has to be installed here,
# at build time. Built for arm64, the architecture the function runs on.
FROM public.ecr.aws/lambda/python:3.14

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install "pytest==9.2.0"

COPY handler.py ${LAMBDA_TASK_ROOT}/

CMD ["handler.handler"]
