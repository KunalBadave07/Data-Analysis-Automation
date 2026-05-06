import os
import time

import boto3

from .logger import get_logger

logger = get_logger()

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
BUCKET_NAME = os.getenv("S3_BUCKET_DATASETS", "retail-sales-analytics-pipeline")


def _create_s3_client():
    # Use the standard boto3 credential chain so keys are never hardcoded in source.
    return boto3.client("s3", region_name=AWS_REGION)


s3_client = _create_s3_client()


def upload_file(local_path, s3_key, retries=3):
    attempt = 0

    while attempt < retries:
        try:
            logger.info(f"Uploading {local_path} to S3 -> {s3_key}")
            s3_client.upload_file(local_path, BUCKET_NAME, s3_key)
            logger.info(f"S3 upload successful: {s3_key}")
            return True
        except Exception as e:
            attempt += 1
            logger.warning(f"S3 upload failed (attempt {attempt}) : {str(e)}")
            time.sleep(2)

    logger.error(f"S3 upload failed after {retries} attempts")
    return False


def download_file(s3_key, local_path, retries=3):
    attempt = 0

    while attempt < retries:
        try:
            logger.info(f"Downloading {s3_key} from S3")
            s3_client.download_file(BUCKET_NAME, s3_key, local_path)
            logger.info("S3 download successful")
            return True
        except Exception as e:
            attempt += 1
            logger.warning(f"S3 download failed (attempt {attempt}) : {str(e)}")
            time.sleep(2)

    logger.error("S3 download failed after retries")
    return False
