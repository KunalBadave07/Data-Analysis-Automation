from __future__ import annotations

import boto3
from flask import current_app


def create_session():
    return boto3.session.Session(region_name=current_app.config["AWS_REGION"])


def get_clients() -> dict[str, object]:
    session = create_session()
    return {
        "s3": session.client("s3"),
        "dynamodb": session.resource("dynamodb"),
        "stepfunctions": session.client("stepfunctions"),
        "lambda": session.client("lambda"),
        "glue": session.client("glue"),
        "athena": session.client("athena"),
        "sagemaker": session.client("sagemaker"),
        "quicksight": session.client("quicksight"),
    }
