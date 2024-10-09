#!/bin/bash

# Fail on error
set -e

# Run download command
uv run python3 /app/s3.py download

# Execute the script
# Create a list from all files in input directory separated by comma
# Run the script for each file in the list
# The script will output the reconstructed video in the output directory

input_files=$(realpath -s /input/* |  tr '\n' ',' | sed 's/,$//')
printf "Input files: $input_files\n"

uv run python3 reconstruct.py \
    --input_video=$input_files \
    --timestamp=$TIMESTAMP \
    --out_dir=/output \
    --fps=$FPS \
    --tmp_dir=/tmp

# Upload the output to S3
uv run python3 /app/s3.py upload
