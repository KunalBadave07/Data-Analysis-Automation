# MANASVI TASK FILE (CRYSTAL CLEAR EXECUTION)
Last updated: 2026-03-10 15:10 IST

This file is your exact checklist. Follow in order.

## 0) Goal
Set up AWS pipeline side completely so Kunal can plug app into real cloud resources.

## 1) IAM HANDOFF TO KUNAL (DO THIS FIRST)
1. Open AWS Console.
2. In top search bar, type `IAM` and open IAM.
3. Left menu -> `Users`.
4. Click `Create user`.
5. User name: `kunal-data-automation`.
6. Click `Next`.
7. In permissions, choose:
   - `Add user to group`
   - `Create group` -> name `data-automation-dev`
8. Attach these policies to group:
   - AmazonS3FullAccess
   - AmazonDynamoDBFullAccess
   - AWSStepFunctionsFullAccess
   - AWSLambda_FullAccess
   - AWSGlueConsoleFullAccess
   - AmazonAthenaFullAccess
   - AmazonSageMakerFullAccess
   - AmazonQuickSightFullAccess
   - CloudWatchLogsFullAccess
9. Finish user creation.
10. Open created user -> `Security credentials`.
11. Under `Access keys`, click `Create access key`.
12. Use case: `CLI`.
13. Copy Access Key ID + Secret Access Key.
14. Send securely to Kunal.

## 2) S3 SETUP
1. AWS search bar -> type `S3` -> open S3.
2. Click `Create bucket`.
3. Bucket name: `data-automation-dev-<unique>`.
4. Region: `ap-south-1`.
5. Keep public access blocked.
6. Enable versioning.
7. Create bucket.
8. Open bucket -> create folders:
   - `raw/uploads/`
   - `processed/glue/`
   - `athena/results/`
   - `models/sagemaker/`
   - `reports/generated/`
   - `quicksight/exports/`
9. Go to `Management` tab -> `Lifecycle rules` -> add rules:
   - Move `raw/uploads/` to IA after 30 days
   - Move `processed/glue/` to IA after 30 days
   - Expire `reports/generated/` after 180 days

## 3) DYNAMODB SETUP
1. AWS search bar -> `DynamoDB`.
2. Click `Create table`.
3. Table name: `analytics_jobs`.
4. Partition key: `job_id` (String).
5. Billing mode: On-demand.
6. Create table.
7. Create optional event table:
   - Table name: `analytics_events`
   - Partition key: `job_id` (String)
   - Sort key: `event_ts` (String)
8. In `analytics_jobs` -> `Indexes` -> create GSIs:
   - `gsi_user_created_at`:
     - PK: `user_id`
     - SK: `created_at`
   - `gsi_status_updated_at`:
     - PK: `status`
     - SK: `updated_at`

## 4) LAMBDA SETUP
Create 4 functions.

### 4.1) Create `da-start-job`
1. Search `Lambda`.
2. Click `Create function`.
3. Author from scratch.
4. Function name: `da-start-job`.
5. Runtime: Python.
6. Create function.
7. Configuration -> Environment variables:
   - `AWS_REGION=ap-south-1`
   - `JOBS_TABLE_NAME=analytics_jobs`
   - `EVENTS_TABLE_NAME=analytics_events`
   - `DATA_BUCKET=<your-bucket>`

### 4.2) Create `da-update-job-status`
Repeat above with function name `da-update-job-status` and same env vars.

### 4.3) Create `da-finalize-results`
Repeat above with function name `da-finalize-results`.

### 4.4) Create `da-handle-failure`
Repeat above with function name `da-handle-failure`.

Notes:
- Use payload examples from:
  - `infra/lambda/payload_examples/start_job_event.json`
  - `infra/lambda/payload_examples/status_update_event.json`

## 5) STEP FUNCTIONS SETUP
1. AWS search -> `Step Functions`.
2. Click `Create state machine`.
3. Choose `Standard`.
4. Name: `analytics-orchestrator-dev`.
5. Definition mode: write code.
6. Copy content from file:
   - `infra/stepfunctions/analytics_orchestrator.asl.json`
7. Replace placeholders:
   - `REPLACE_BUCKET` -> your real bucket
   - ensure Lambda function names match your created ones
8. Create state machine.
9. Copy state machine ARN (send to Kunal).

## 6) GLUE SETUP
1. AWS search -> `Glue`.
2. Open `Crawlers` -> `Create crawler`.
3. Name: `da-raw-crawler`.
4. Data source: `s3://<bucket>/raw/uploads/`.
5. IAM role: create/select Glue service role.
6. Target database: create `analytics_raw`.
7. Schedule: On demand.
8. Create crawler.
9. Go to `Jobs` -> `Create job`.
10. Name: `da-etl-job`.
11. Script: basic ETL placeholder.
12. Input: raw upload prefix.
13. Output: `s3://<bucket>/processed/glue/`.
14. Save job.

## 7) ATHENA SETUP
1. AWS search -> `Athena`.
2. Open `Workgroups` -> `Create workgroup`.
3. Name: `data-automation-wg`.
4. Set query result location:
   - `s3://<bucket>/athena/results/`
5. Save workgroup.
6. Query editor -> choose workgroup.
7. Use SQL from:
   - `infra/athena/query_templates.sql`
8. Run at least one query successfully.

## 8) QUICKSIGHT SETUP (PLACEHOLDER NOW)
1. AWS search -> `QuickSight`.
2. If not activated, complete subscription setup.
3. Create data source -> Athena.
4. Connect to `data-automation-wg`.
5. Create a dataset from Athena table.
6. Create dashboard placeholder with:
   - KPI visual
   - trend visual
   - table visual
7. Save dashboard and copy dashboard ID.

## 9) CLOUDWATCH MONITORING
1. AWS search -> `CloudWatch`.
2. Verify log groups for all Lambda functions exist.
3. Create alarms:
   - Step Functions failures > 0 in 5 min
   - Lambda errors > 0 in 5 min
4. Save alarm names for handoff.

## 10) WHAT YOU MUST SEND BACK TO KUNAL
Send this exact list:
1. S3 bucket name.
2. S3 prefix layout used.
3. DynamoDB table names and GSIs.
4. Step Functions ARN.
5. Lambda names and ARNs.
6. Glue crawler/job names.
7. Athena workgroup + query output location.
8. QuickSight dataset/dashboard IDs.
9. CloudWatch alarm names.
10. IAM credentials for Kunal (secure method only).

## 11) CODEx CONTINUITY RULES (MANDATORY)
When your Codex works on this project, it must:
1. Update `MANASVI_CODEX_CONTEXT.md`.
2. Update `ToDo.txt` with timestamped entries.
3. Update `DevInstructions.txt` with real AWS values/steps.
4. Keep prior logs, append only.
5. After code changes, run:
   - `python -m pytest -q`
