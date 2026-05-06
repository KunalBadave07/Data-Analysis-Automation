from __future__ import annotations

import os

from app.services.analytics_service import generate_analysis

from .data_validation import run_data_validation
from .logger import generate_run_id, get_logger
from .preprocessing import (
    clean_dataset,
    feature_engineering,
    handle_outliers,
    load_dataset,
    save_processed_dataset,
)
from .s3_utils import upload_file

logger = get_logger()


def run_pipeline(file_path, operation, category="all", region="all", year="all"):
    run_id = generate_run_id()

    try:
        logger.info(f"RUN_ID={run_id} | Pipeline started")
        df = load_dataset(file_path)

        logger.info(f"RUN_ID={run_id} | Uploading raw dataset to S3")
        upload_file(file_path, f"raw-data/{os.path.basename(file_path)}")

        logger.info(f"RUN_ID={run_id} | Cleaning dataset")
        df, cleaning_notes = clean_dataset(df)

        logger.info(f"RUN_ID={run_id} | Running data validation")
        validation = run_data_validation(df)
        if not validation["passed"]:
            raise ValueError("; ".join(validation["issues"]))

        logger.info(f"RUN_ID={run_id} | Inspecting outliers")
        df, outlier_notes = handle_outliers(df)

        logger.info(f"RUN_ID={run_id} | Creating derived features")
        df, feature_notes = feature_engineering(df)

        base_name = os.path.basename(file_path).rsplit(".", 1)[0]
        processed_path = f"data/processed/{base_name}_processed.csv"
        os.makedirs(os.path.dirname(processed_path), exist_ok=True)

        logger.info(f"RUN_ID={run_id} | Saving processed dataset")
        save_processed_dataset(df, processed_path)

        if os.path.exists(processed_path):
            upload_file(processed_path, f"processed-data/{os.path.basename(processed_path)}")
            logger.info(f"RUN_ID={run_id} | Processed dataset uploaded to S3")
        else:
            logger.error(f"RUN_ID={run_id} | Processed file missing, upload skipped")

        logger.info(f"RUN_ID={run_id} | Generating analytics for {operation}")
        processing_notes = {}
        processing_notes.update(cleaning_notes)
        processing_notes.update(outlier_notes)
        processing_notes.update(feature_notes)
        processing_notes["validation_issues"] = validation["issues"]
        processing_notes["validation_summary"] = validation.get("summary", {})
        processing_notes["validation_warnings"] = validation.get("warnings", [])

        analysis = generate_analysis(
            df,
            operation,
            category=category,
            region=region,
            year=year,
            processing_notes=processing_notes,
        )
        analysis["processing_notes"] = processing_notes
        analysis["processed_path"] = processed_path
        return analysis

    except Exception as e:
        logger.error(f"RUN_ID={run_id} | Pipeline failed: {str(e)}")
        raise
