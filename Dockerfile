ARG BASE_IMAGE=ghcr.io/josauder/mee-deepreefmap:1.1.0
FROM ${BASE_IMAGE}

# Install the dependencies
USER root
RUN uv add boto3==1.35.36 pydantic-settings==2.5.2
USER 1000


# Expose the base image as an environment variable at runtime
ARG BASE_IMAGE
ENV BASE_IMAGE=${BASE_IMAGE}

COPY --chown=1000:1000 s3.py execute_from_s3.sh /app/
WORKDIR /app/src

ENTRYPOINT ["/bin/bash", "/app/execute_from_s3.sh"]
