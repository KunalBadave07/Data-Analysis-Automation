# Cloud Analytics Platform Architecture

## End-to-End Flow
1. User registers/logs in.
2. User uploads dataset + selects operation.
3. Flask API stores metadata and sends payload to AWS Step Functions.
4. Step Functions orchestrates Lambda, Glue ETL, Athena SQL, feature engineering, and SageMaker training/inference.
5. Model outputs are transformed by the GenAI Insight Engine into business-readable recommendations.
6. QuickSight dashboard is generated/updated.
7. Final artifacts (insights, dashboard links, downloadable report) are returned to Flask.
8. User sees status, results, dashboard, and history.

## Primary AWS Data Path
`Upload -> S3 -> Step Functions -> Lambda -> Glue -> Athena -> SageMaker -> GenAI -> QuickSight -> API response`

## System Components
- `Flask Web + API`: session/auth, uploads, status APIs, history, report pages.
- `DynamoDB`: users, job metadata, execution status, links to artifacts.
- `S3`: raw uploads, transformed datasets, model outputs, generated reports.
- `Step Functions`: orchestration backbone with retries and failure routing.
- `Lambda`: event handlers and control-plane functions.
- `Glue`: schema discovery, ETL jobs, catalog updates.
- `Athena`: ad-hoc/templated analytics queries.
- `SageMaker`: model training/inference jobs.
- `QuickSight`: BI dashboards and embeddings.
- `GenAI Insight Engine`: transforms numerical output into actionable narrative.

## Security Model (Target)
- IAM least privilege for each service role.
- App secrets in AWS Secrets Manager / Parameter Store.
- S3 bucket policies scoped to service roles and prefixes.
- Signed URLs for dataset/report access.
- Audit trail through CloudWatch + CloudTrail + DynamoDB job logs.

## Team Split
- `Kunal`: Frontend, ML models, SageMaker integration, API integration.
- `Manasvi`: AWS pipeline (Lambda, Step Functions, Glue, Athena), IAM policy setup.
- Mandatory handoff: Manasvi must provide Kunal IAM access with scoped permissions for integration/testing.

## Phase 1 Scope
- Flask monolith scaffold with route/page skeletons.
- Local stub pipeline to unblock frontend and API integration.
- Project docs and setup runbook.
- No real AWS execution in this phase.
