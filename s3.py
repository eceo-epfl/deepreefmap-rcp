import boto3
import os
from pydantic_settings import BaseSettings
import argparse
import sys


class Config(BaseSettings):
    # S3 settings
    S3_URL: str
    S3_BUCKET_ID: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str

    # Key to prefix to all assets in the S3 bucket. Should be distinct to the
    # deployment as to avoid conflicts
    S3_PREFIX: str

    INPUT_OBJECT_IDS: list[str]
    SUBMISSION_ID: str
    FPS: int
    TIMESTAMP: str

    CLI_CHOICES: list[str] = ["upload", "download"]

    # Input is system root /input
    INPUT_FOLDER: str = os.path.join(os.path.abspath(os.sep), "input")
    OUTPUT_FOLDER: str = os.path.join(os.path.abspath(os.sep), "output")

    # The following are encoded in the Dockerfile and are used to output the
    # version of the software used in the container at runtime
    BASE_IMAGE: str  # This is probably already in the Dockerfile


config = Config()


def download_from_s3(
    s3: boto3.client,
) -> None:
    """Downloads all files from the S3 bucket to the /input folder

    The files are placed in the /input folder with the same name as the asset
    """

    print(f"Downloading assets from S3 bucket {config.S3_BUCKET_ID}")

    if len(config.INPUT_OBJECT_IDS) == 0:
        raise ValueError("No input files to download")

    # Download the assets from S3
    for asset in config.INPUT_OBJECT_IDS:
        print(f"Downloading {asset}")
        s3.download_file(
            config.S3_BUCKET_ID,
            f"{config.S3_PREFIX}/inputs/{asset}",
            os.path.join(config.INPUT_FOLDER, asset),
        )


def upload_to_s3(
    s3: boto3.client,
) -> None:
    """Uploads all files from the /output folder to the S3 bucket

    The files are places in the submission IDs folder in /output
    """

    print(f"Uploading assets to S3 bucket {config.S3_BUCKET_ID}")
    count = 0  # Count the number of files uploaded

    for output in os.listdir(config.OUTPUT_FOLDER):
        # Handle folders by appending the folder name to the output filename
        if os.path.isdir(os.path.join(config.OUTPUT_FOLDER, output)):
            print(f"Entering folder: {output}")
            for file in os.listdir(os.path.join(config.OUTPUT_FOLDER, output)):
                print(f"Uploading {output}-{file}")
                s3.upload_file(
                    os.path.join(
                        os.path.join(config.OUTPUT_FOLDER, output, file)
                    ),
                    config.S3_BUCKET_ID,
                    f"{config.S3_PREFIX}/outputs/"
                    f"{config.SUBMISSION_ID}/{output}-{file}",
                )
                count += 1
        else:
            print(f"Uploading {output}")
            s3.upload_file(
                os.path.join(os.path.join(config.OUTPUT_FOLDER, output)),
                config.S3_BUCKET_ID,
                f"{config.S3_PREFIX}/outputs/{config.SUBMISSION_ID}/{output}",
            )
            count += 1

    if count == 0:
        raise ValueError("No output files to upload")


def delete_all_output_files(
    s3: boto3.client,
) -> None:
    """Deletes all files from the output S3 bucket"""

    print(
        f"Deleting all output files from S3 bucket {config.S3_BUCKET_ID}"
        f" for submission {config.SUBMISSION_ID}"
    )

    # List all objects in the output folder
    response = s3.list_objects_v2(
        Bucket=config.S3_BUCKET_ID,
        Prefix=f"{config.S3_PREFIX}/outputs/{config.SUBMISSION_ID}/",
    )

    # Delete all objects
    for obj in response.get("Contents", []):
        print(f"Deleting {obj['Key']}")
        s3.delete_object(
            Bucket=config.S3_BUCKET_ID,
            Key=obj["Key"],
        )


if __name__ == "__main__":
    # Use CLI arguments upload or download to select function

    print("\nConfiguration:")
    print("-----------------")
    for key in [
        "INPUT_OBJECT_IDS",
        "SUBMISSION_ID",
        "FPS",
        "TIMESTAMP",
        "BASE_IMAGE",
    ]:
        print(f"\t{key:20}: {getattr(config, key)}")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=config.CLI_CHOICES,
        help="Action to perform",
    )
    args = parser.parse_args()

    # Check that the folders exist before starting
    for folder in [config.INPUT_FOLDER, config.OUTPUT_FOLDER]:
        if not os.path.exists(folder):
            raise FileNotFoundError(
                f"Folder {folder} not found",
            )

    s3 = boto3.client(
        "s3",
        aws_access_key_id=config.S3_ACCESS_KEY,
        aws_secret_access_key=config.S3_SECRET_KEY,
        endpoint_url=f"https://{config.S3_URL}",
    )

    try:
        if args.action == "upload":
            upload_to_s3(s3)
        elif args.action == "download":
            delete_all_output_files(s3)
            download_from_s3(s3)
        else:
            raise ValueError(
                f"Invalid CLI action, acceptable choices are {config.CLI_CHOICES}"
            )

        print("Done")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
