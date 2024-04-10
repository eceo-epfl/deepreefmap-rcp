FROM python:3.10-slim

# Set commit hash for gpmfstream repo as there are no versions
ARG GPMFSTREAM_GIT_HASH=f1a9742
ARG DEEPREEF_GIT_HASH=dcd0a70db238f10fc49009d2377e76caa29adb02

RUN apt-get update && \
    apt-get install -y git wget unzip build-essential \
    curl ffmpeg libsm6 libxext6 && \
    pip install poetry pybind11

RUN git clone https://github.com/josauder/mee-deepreefmap.git /app
WORKDIR /app
RUN git checkout ${DEEPREEF_GIT_HASH}

# # Get the gpmfstream library
WORKDIR /app

RUN git clone https://github.com/hovren/gpmfstream.git
WORKDIR /app/gpmfstream
RUN git checkout ${GPMFSTREAM_GIT_HASH} && git submodule update --init && python setup.py install

# Copy the pyproject.toml and poetry.lock files to the container
WORKDIR /app

# Download the example data and checkpoints
RUN curl -f -L -o example_data.zip https://zenodo.org/records/10624794/files/example_data.zip?download=1 && unzip example_data.zip example_data/checkpoints/* && rm -rf example_data.zip

# Change to non-root user
RUN groupadd mygroup --gid 1000 && \
    useradd -m -U -s /bin/bash -G mygroup -u 1000 myuser && \
    chown -R 1000:1000 /app && \
    chmod -R 755 /app && \
    mkdir /output /input && \
    chown -R 1000:1000 /output /input /tmp /app

USER 1000

# Install the dependencies
RUN poetry install --no-root --no-dev

COPY --chown=1000:1000 s3.py execute_from_s3.sh /app/
WORKDIR /app/src

ENTRYPOINT ["/bin/bash", "/app/execute_from_s3.sh"]
