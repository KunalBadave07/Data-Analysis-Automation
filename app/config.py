import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

    # AWS resources (to be wired in later phases)
    S3_BUCKET_DATASETS = os.getenv("S3_BUCKET_DATASETS", "")
    DYNAMODB_TABLE_USERS = os.getenv("DYNAMODB_TABLE_USERS", "analytics_users")
    DYNAMODB_TABLE_JOBS = os.getenv("DYNAMODB_TABLE_JOBS", "analytics_jobs")
    STEP_FUNCTION_ARN = os.getenv("STEP_FUNCTION_ARN", "")
    LAMBDA_TRIGGER_NAME = os.getenv("LAMBDA_TRIGGER_NAME", "")
    ATHENA_WORKGROUP = os.getenv("ATHENA_WORKGROUP", "primary")
    GLUE_DATABASE = os.getenv("GLUE_DATABASE", "analytics_raw")
    SAGEMAKER_ROLE_ARN = os.getenv("SAGEMAKER_ROLE_ARN", "")
    QUICKSIGHT_NAMESPACE = os.getenv("QUICKSIGHT_NAMESPACE", "default")

    # Email/OTP placeholders for Phase 3
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_SENDER = os.getenv("SMTP_SENDER", os.getenv("SMTP_USERNAME", "no-reply@data-automation.local"))

    # Local authentication persistence for pre-AWS phases
    AUTH_DB_PATH = os.getenv("AUTH_DB_PATH", "instance/data_automation.db")
    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
    OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", "45"))
