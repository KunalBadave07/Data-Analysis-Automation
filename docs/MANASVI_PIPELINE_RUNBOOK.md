# Manasvi AWS Pipeline Runbook (Detailed)

## Objective
Build and hand over the AWS automation backbone so Kunal can integrate frontend/API with real cloud execution.

Target pipeline:
`Flask Upload -> S3 -> Step Functions -> Lambda -> Glue -> Athena -> SageMaker -> GenAI -> QuickSight -> Flask Results`

## Scope Owned By Manasvi
- IAM access handoff to Kunal
- S3 storage layout and policies
- DynamoDB job/status persistence schema
- Lambda functions
- Step Functions orchestration
- Glue crawler/job setup
- Athena workgroup/query output setup
- QuickSight data plane setup (dataset/analysis/dashboard placeholder)
- CloudWatch logs and alarms

## Prerequisites
- AWS account access with admin-equivalent setup rights.
- Region decided (`ap-south-1` recommended).
- Existing project files from this repo.

## Final Handoff Artifacts (Must Provide)
1. IAM user credentials for Kunal (Access Key ID + Secret via secure channel).
2. S3 bucket name and folder convention.
3. DynamoDB table names and keys.
4. Step Functions state machine ARN.
5. Lambda function names/ARNs.
6. Glue crawler + job names.
7. Athena workgroup/database/output location.
8. QuickSight dashboard/dataset IDs.
9. CloudWatch alarm names and thresholds.

---

## Phase A: IAM and Security
### A1) Create Kunal IAM user
1. IAM -> Users -> Create user.
2. User name: `kunal-data-automation`.
3. Access type: programmatic.
4. Add to group `data-automation-dev`.

### A2) Temporary development policy set
Attach these managed policies temporarily:
- `AmazonS3FullAccess`
- `AmazonDynamoDBFullAccess`
- `AWSStepFunctionsFullAccess`
- `AWSLambda_FullAccess`
- `AWSGlueConsoleFullAccess`
- `AmazonAthenaFullAccess`
- `AmazonSageMakerFullAccess`
- `AmazonQuickSightFullAccess`
- `CloudWatchLogsFullAccess`

### A3) Security hardening plan (after MVP)
- Replace full-access policies with least-privilege custom policies.
- Rotate keys every 30-60 days.
- Move secrets to Secrets Manager/Parameter Store.

---

## Phase B: S3 Foundation
### B1) Bucket setup
1. S3 -> Create bucket.
2. Example name: `data-automation-dev-<unique-suffix>`.
3. Region: `ap-south-1`.
4. Keep Block Public Access ON.
5. Versioning: ON.

### B2) Prefix structure
Create prefixes:
- `raw/uploads/`
- `processed/glue/`
- `athena/results/`
- `models/sagemaker/`
- `reports/generated/`
- `quicksight/exports/`

### B3) Lifecycle
- `raw/uploads/*`: transition to IA after 30 days.
- `processed/*`: transition to IA after 30 days.
- `reports/generated/*`: expire after 180 days.

---

## Phase C: DynamoDB Schema
### C1) Table: `analytics_jobs`
- Partition key: `job_id` (String)
- Attributes stored:
  - `job_id`
  - `user_id`
  - `filename`
  - `operation`
  - `description`
  - `status` (`QUEUED|RUNNING|SUCCEEDED|FAILED`)
  - `execution_arn`
  - `s3_input_key`
  - `s3_processed_key`
  - `created_at`
  - `updated_at`
  - `error_message` (optional)

### C2) GSI recommendations
- `gsi_user_created_at`
  - PK: `user_id`
  - SK: `created_at`
- `gsi_status_updated_at`
  - PK: `status`
  - SK: `updated_at`

### C3) Table: `analytics_events` (optional but recommended)
- PK: `job_id`
- SK: `event_ts`
- Purpose: stage-by-stage timeline for status page.

---

## Phase D: Lambda Functions
Create these functions (Python 3.13 or latest stable runtime in your account):

1. `da-start-job`
- Input: upload metadata from Flask.
- Tasks:
  - write initial `analytics_jobs` item (`QUEUED`)
  - call `StartExecution` on Step Functions
  - update job with `execution_arn`
- Output: `{job_id, execution_arn, status}`

2. `da-update-job-status`
- Input: stage updates from state machine.
- Tasks:
  - set status in DynamoDB
  - update `updated_at`
  - append event to `analytics_events` (if enabled)

3. `da-finalize-results`
- Input: final artifacts (S3 keys, metrics, insight references).
- Tasks:
  - mark `SUCCEEDED` or `FAILED`
  - save result pointers for Flask results endpoint.

4. `da-handle-failure`
- Input: error payload from Catch blocks.
- Tasks:
  - mark failed status
  - persist error reason
  - emit CloudWatch structured log.

Set environment variables on all Lambdas:
- `AWS_REGION`
- `JOBS_TABLE_NAME`
- `EVENTS_TABLE_NAME` (if used)
- `DATA_BUCKET`

---

## Phase E: Step Functions
Use this template: `infra/stepfunctions/analytics_orchestrator.asl.json`

Execution flow:
1. Initialize job (`da-update-job-status` -> RUNNING).
2. Trigger Glue ETL job.
3. Run Athena query.
4. Trigger SageMaker (placeholder task initially).
5. Finalize result (`da-finalize-results`).
6. Catch any failure -> `da-handle-failure`.

Deliver ARN to Kunal for `.env`:
- `STEP_FUNCTION_ARN=<state-machine-arn>`

---

## Phase F: Glue + Athena
### F1) Glue crawler
- Data source: `s3://<bucket>/raw/uploads/`
- Database: `analytics_raw`
- Schedule: on demand (for MVP)

### F2) Glue job
- Name: `da-etl-job`
- Input: raw upload prefix
- Output: `processed/glue/`
- Write parquet for Athena performance

### F3) Athena
- Workgroup: `data-automation-wg`
- Query result location:
  `s3://<bucket>/athena/results/`
- Database: `analytics_raw` (crawler output) + optional `analytics_curated`

Use query templates from:
- `infra/athena/query_templates.sql`

---

## Phase G: QuickSight
1. QuickSight account setup (same region or supported region).
2. Create data source from Athena workgroup.
3. Create dataset for model outputs / curated analytics table.
4. Build minimal dashboard placeholder:
   - KPI card
   - trend line
   - anomaly table
5. Save dashboard ID and (later) embed config details for Kunal.

---

## Phase H: Monitoring and Reliability
### H1) CloudWatch logs
- Enable logs for each Lambda.
- Enable execution logging for Step Functions.

### H2) Alarms
Create alarms:
1. Step Functions failed executions > 0 in 5 min.
2. Any Lambda errors > 0 in 5 min.
3. Lambda duration p95 anomaly (optional).

### H3) Retry policies
- Step Functions task retry:
  - `MaxAttempts`: 2-3
  - backoff strategy on transient failures.

---

## Integration Contract for Kunal
Manasvi must share:
- `S3_BUCKET_DATASETS`
- `DYNAMODB_TABLE_JOBS`
- `STEP_FUNCTION_ARN`
- `GLUE_DATABASE`
- `ATHENA_WORKGROUP`
- Lambda names/ARNs if direct invoke is needed.

Payload contract for job start request (from Flask):
```json
{
  "job_id": "uuid",
  "user_id": "uuid",
  "filename": "sales.csv",
  "operation": "forecasting",
  "description": "optional free text",
  "s3_input_key": "raw/uploads/<job_id>/sales.csv",
  "created_at": "ISO8601"
}
```

---

## Acceptance Checklist (Sign-off)
- [ ] Kunal can run `aws sts get-caller-identity` with provided credentials.
- [ ] Upload test file reaches S3 raw prefix.
- [ ] Step Functions execution starts and finishes (success/failure both handled).
- [ ] DynamoDB status updates visible for all stages.
- [ ] Glue and Athena path runs at least once.
- [ ] CloudWatch logs and alarms visible.
- [ ] All ARNs/names shared to Kunal.

---

## Fast Start Order (Recommended)
1. IAM handoff
2. S3 + DynamoDB
3. Step Functions + Lambda skeleton
4. Glue + Athena
5. Monitoring
6. QuickSight placeholder
7. Handoff package to Kunal
