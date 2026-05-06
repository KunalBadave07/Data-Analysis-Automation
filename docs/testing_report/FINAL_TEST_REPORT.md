# Retail Sales Analytics Pipeline - QA Validation Report

## Project Overview
This repository is a Flask-based retail sales analytics application with local authentication, dataset upload, preprocessing, analytics generation, dashboard rendering, report generation, and partial AWS helper modules. The documentation describes a broader cloud pipeline using S3, Step Functions, Lambda, Glue, Athena, SageMaker, and QuickSight, but the executable codebase currently implements only a subset of that architecture.

## Objective
Validate the implemented system with executable automated tests, identify production risks, and separate:
- verified working behavior
- mocked/local-only behavior
- documented but non-implemented cloud/ML behavior

## Testing Environment
- OS: Windows (`win32`)
- Python: `3.13.3`
- Test runner: `pytest 8.3.4`
- Coverage plugin: `pytest-cov 7.1.0`
- Flask: `3.1.0`
- Execution mode: local Flask app + mocked cloud boundaries where runtime integrations do not exist
- Evidence files:
- `test_logs/pytest_run.log`
- `test_logs/junit.xml`
- `coverage_report/coverage.xml`
- `coverage_report/html/index.html`

## Scope Covered
### Executed and validated
- Flask routes
- Authentication flow
- Dataset upload route behavior
- Dataset preprocessing
- Dataset validation
- Data mapping / schema inference
- Analytics generation
- Dashboard payload generation
- Report context generation
- Local pipeline execution
- AWS client factory wrappers
- S3 upload retry behavior
- Infra contract files (`ASL`, sample Lambda payloads, Athena SQL template)

### Not executable in current codebase
- Real Lambda trigger execution
- Real Glue ETL job invocation
- Real Athena query execution
- Real SageMaker training/inference invocation
- Real QuickSight embedding/export flow
- Real Power BI export

## Test Execution Summary
- Total tests executed: `35`
- Total passed: `35`
- Total failed: `0`
- Coverage: `81%`
- Test result: `PASS` for implemented local code paths
- Delivery readiness: `NOT READY` for the full advertised cloud pipeline due to missing runtime integrations and security issues

## Unit Testing Results
### Route and UI behavior
- `analysis`, `dataset`, `auth`, `main`, health, and page routes were exercised.
- Results, dashboard, and report pages render correctly for seeded successful jobs.
- Upload requires authentication and redirects correctly.

### Data and analytics behavior
- Dynamic schema inference works for flexible column names like `order_date`, `qty`, `unit_price`, `product_line`, and `state`.
- Preprocessing normalizes columns, detects date-like fields, and builds derived time features.
- Validation catches empty datasets and warns when no numeric fields exist.
- Dashboard and report payloads are generated from real CSV data.

### Cloud/helper behavior
- AWS client wrapper returns expected service objects.
- S3 upload helper retry behavior works under simulated transient failure.
- Step Functions JSON, Lambda payload examples, and Athena SQL template are syntactically valid artifacts.

## System Testing Results
Real system testing was limited to the code paths that exist locally. The executed end-to-end test covered:

`login -> upload -> local pipeline -> processing -> results -> dashboard -> report`

This flow passed using the real Flask routes, real pipeline logic, and mocked S3 upload success. The broader documented AWS orchestration path could not be executed because the codebase does not currently contain runnable service-layer orchestration for Step Functions, Lambda, Glue, Athena, SageMaker, or QuickSight.

## Coverage
- Overall application coverage: `81%`
- Strongest areas:
- preprocessing / validation / analytics services
- dataset and analysis routes
- auth storage and OTP service
- Lower coverage areas:
- `app/routes/auth.py`
- `app/routes/main.py`
- `app/routes/analysis.py`
- `app/services/pipeline/s3_utils.py`

See `coverage_report/html/index.html` for line-level details.

## Bugs Found
| ID | Severity | Area | Finding | Status |
| --- | --- | --- | --- | --- |
| DEF-01 | Critical | Security / AWS | Hardcoded AWS access key and secret are present in `app/services/pipeline/s3_utils.py`. | Open |
| DEF-02 | Critical | Cloud Orchestration | The advertised Step Functions -> Lambda -> Glue -> Athena -> SageMaker runtime path is not implemented in executable Flask/service code. | Open |
| DEF-03 | High | Persistence | `pipeline_stub.py` stores jobs in in-memory `JOBS`, so job state is lost on restart and is not production-safe. | Open |
| DEF-04 | High | Reliability | `run_pipeline()` calls `upload_file()` but does not fail fast when S3 upload returns `False`; upload failures can be silently tolerated. | Open |
| DEF-05 | High | ML Delivery | No executable ML prediction/training service exists despite project claims; only static output artifacts are present under `app/ml_models/outputs`. | Open |
| DEF-06 | High | System Integration | No executable Lambda trigger, Glue job launcher, Athena query runner, SageMaker invoker, or QuickSight embed service exists. | Open |
| DEF-07 | Medium | Upload Safety | Uploaded files are written with original names into `data/raw`, creating overwrite/collision risk. | Open |
| DEF-08 | Medium | Validation | Data validation is minimal and does not enforce business rules, schema contracts, or stronger quality checks. | Open |
| DEF-09 | Medium | Dashboard Export | PNG and print/PDF export exist, but no true QuickSight or Power BI-style export artifact exists. | Open |
| DEF-10 | Medium | Maintainability | Architecture documentation overstates implemented capabilities, creating delivery and QA expectation mismatch. | Open |
| DEF-11 | Low | Resource Handling | SQLite connections in auth storage were left open during tests; fixed during this QA pass by explicitly closing connections. | Resolved in QA pass |

## Risk Analysis
### Production blockers
- Hardcoded AWS credentials create immediate security exposure and potential account compromise.
- The cloud pipeline described in docs is not actually wired into runtime code, so the full advertised product flow cannot be deployed as-is.
- In-memory job storage means active analyses disappear after process restart.

### Data quality risks
- Validation is too permissive for a business analytics platform; malformed or semantically wrong datasets may still pass.
- Dynamic mapping is improved, but there is no domain-level verification that the inferred primary metric is always the correct business metric.

### Operational risks
- S3 failures can be logged without halting the analysis flow.
- No retry/orchestration logic exists for Lambda, Glue, Athena, or SageMaker because the runtime path itself is missing.

### Data leakage risks
- Raw and processed datasets are uploaded directly to S3 using embedded credentials.
- No signed URL, secrets manager, or environment-only credential pattern is enforced in the current S3 utility.

## Screenshots References
- No browser screenshots were captured in this run.
- Evidence folder: `screenshots/README.md`

## Recommendations
1. Remove hardcoded AWS credentials immediately and replace them with environment variables or IAM role-based auth.
2. Replace `pipeline_stub.JOBS` with durable storage before any production deployment.
3. Implement real service-layer integrations for Step Functions, Lambda, Glue, Athena, SageMaker, and QuickSight, then add integration tests against those clients.
4. Make S3 upload failure fatal or explicitly state degraded mode when uploads fail.
5. Add stronger schema and business validation rules for uploaded datasets.
6. Add filename sanitization and unique upload naming to prevent collisions.
7. Build a real ML service module if ML forecasting is part of the promised deliverable.
8. Expand auth and user-portal coverage to close the remaining branch gaps.

## Final Conclusion
The implemented local Flask analytics application has been genuinely validated and is in solid shape for its current local-scope behavior: upload, preprocessing, dynamic analytics, dashboard generation, reporting, and authentication all passed automated testing. However, the full cloud-based retail analytics pipeline described in the project brief is not yet production-ready because major AWS and ML runtime integrations are either mocked, static, or absent from the executable codebase.

The local application layer is test-validated.
The full advertised cloud pipeline is not yet test-complete or deployment-ready.
