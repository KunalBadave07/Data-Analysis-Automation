# Phase 1: System Architecture and Repository Setup

## 1) Architecture Explanation
Phase 1 establishes a production-style foundation where frontend pages, API routes, service boundaries, and docs are ready before cloud wiring. The app currently uses a local in-memory pipeline stub so Kunal and Manasvi can develop in parallel without waiting for full AWS infra.

Current execution path:
`Upload Form -> Flask Route -> pipeline_stub -> Processing -> Results -> Dashboard -> Report -> History`

Target cloud path (next phases):
`Upload -> S3 -> Step Functions -> Lambda/Glue/Athena/SageMaker -> GenAI -> QuickSight -> Flask API`

## 2) Folder Structure
```text
Data Automation/
  app/
    __init__.py
    config.py
    extensions.py
    routes/
      main.py
      auth.py
      dataset.py
      analysis.py
    services/
      aws_clients.py
      pipeline_stub.py
      report_service.py
    static/
      css/styles.css
      js/main.js
    templates/
      base.html
      home.html
      operation_select.html
      upload.html
      processing.html
      results.html
      dashboard.html
      report.html
      history.html
      auth/
        login.html
        register.html
  docs/
    architecture.md
    PHASE_01.md
  tests/
    test_health.py
  .env.example
  .gitignore
  DevInstructions.txt
  README.md
  ToDo.txt
  requirements.txt
  run.py
```

## 3) Code Generation
Implemented in this phase:
- Flask app factory with environment config and extension initialization.
- Route blueprints for all required pages in user flow.
- Auth skeleton with `Flask-Login` + `Flask-Bcrypt`.
- In-memory pipeline stub to mimic automated pipeline behavior.
- Reusable report generation service.
- Tailwind-based responsive Jinja UI with animations.
- Health test via `pytest`.

## 4) Required Commands
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Test command:
```powershell
pytest -q
```

## 5) AWS Setup Instructions (Phase 1 Prep)
1. Create/confirm AWS account and set region (recommended `ap-south-1`).
2. Create S3 bucket for datasets (name must be globally unique).
3. Create DynamoDB tables:
   - `analytics_users` (PK: `user_id`)
   - `analytics_jobs` (PK: `job_id`)
4. Manasvi creates IAM user/group for Kunal with programmatic access.
5. Attach minimum policies for now:
   - `AmazonS3FullAccess` (temporary for development)
   - `AmazonDynamoDBFullAccess` (temporary)
   - `AWSStepFunctionsFullAccess` (temporary)
   - `AWSLambda_FullAccess` (temporary)
   - `AWSGlueConsoleFullAccess` (temporary)
   - `AmazonAthenaFullAccess` (temporary)
   - `AmazonSageMakerFullAccess` (temporary)
   - `AmazonQuickSightFullAccess` (temporary)
6. Save Access Key ID and Secret Access Key securely for Kunal.
7. Fill `.env` placeholders.

## 6) Integration Instructions
1. Update `.env` with AWS resource names/ARNs.
2. Keep `pipeline_stub` active until Step Functions workflow is ready.
3. In Phase 5, replace `start_pipeline()` implementation to:
   - Upload to S3.
   - Write job metadata to DynamoDB.
   - Trigger Step Functions execution.
4. Add status polling endpoint reading from DynamoDB.

## 7) Testing Instructions
Phase 1 checks:
1. `GET /health` returns `{"status":"ok","phase":1}`.
2. Register and login works locally.
3. Upload flow creates mock job and navigates to results.
4. History page lists prior jobs for current session.
5. `pytest -q` passes at least one test (`test_health.py`).
