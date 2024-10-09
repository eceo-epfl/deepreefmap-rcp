FROM ghcr.io/josauder/mee-deepreefmap:1.1.0

# Install the dependencies
USER root
RUN uv add boto3==1.35.36 pydantic-settings==2.5.2
USER 1000

COPY --chown=1000:1000 s3.py execute_from_s3.sh /app/
WORKDIR /app/src

ENTRYPOINT ["/bin/bash", "/app/execute_from_s3.sh"]
