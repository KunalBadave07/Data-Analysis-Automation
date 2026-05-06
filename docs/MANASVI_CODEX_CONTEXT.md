# MANASVI CODEX CONTEXT FILE
Last updated: 2026-03-10 15:10 IST

## Read This First
This file is for **Codex running on Manasvi's PC** after project ZIP transfer.

Primary goal for Manasvi's Codex:
1. Continue only AWS pipeline ownership work.
2. Keep project continuity with existing architecture.
3. Update tracking files after every meaningful change:
   - `ToDo.txt`
   - `DevInstructions.txt`
   - `MANASVI_CODEX_CONTEXT.md` (this file)

---

## Project Summary
- Project: Cloud-based automated data analytics platform.
- Frontend/backend app: Flask + Jinja + Tailwind + JS.
- Current local pipeline behavior: stubbed in `app/services/pipeline_stub.py`.
- Cloud target path:
  `Upload -> S3 -> Step Functions -> Lambda -> Glue -> Athena -> SageMaker -> GenAI -> QuickSight -> Results`.

---

## Current State (As of 2026-03-10 15:10 IST)
Completed phases:
1. Phase 1: Architecture + repo scaffold.
2. Phase 2: Frontend UI framework hardening.
3. Phase 3: Authentication + OTP verification with local persistence.

Current blocker:
- Real AWS integration cannot proceed until Manasvi completes cloud tasks and shares IAM/resource details with Kunal.

Existing cloud guidance already in repo:
- `docs/MANASVI_PIPELINE_RUNBOOK.md`
- `infra/stepfunctions/analytics_orchestrator.asl.json`
- `infra/lambda/payload_examples/start_job_event.json`
- `infra/lambda/payload_examples/status_update_event.json`
- `infra/athena/query_templates.sql`

---

## Work Split (Ground Truth)
### What Kunal has already done
- Built and tested local application foundation.
- Built responsive frontend and full user flow pages.
- Built auth system with OTP verification.
- Maintained docs/logging files and test suite.

### What Codex (Kunal session) has already done
- Implemented phases 1-3 code.
- Added detailed AWS runbook for Manasvi.
- Added infra templates for Step Functions/Lambda/Athena.
- Maintained `ToDo.txt`, `DevInstructions.txt`, and docs.

### What Manasvi has done so far
- Not yet completed AWS implementation artifacts in this repo context.

### What Manasvi must do now
- Complete all AWS pipeline tasks listed in `docs/MANASVI_PIPELINE_RUNBOOK.md`.
- Share final artifact package back to Kunal.

---

## Non-Negotiable Continuity Rules For Manasvi's Codex
1. After every significant action, append timestamped entry in `ToDo.txt`.
2. Keep `DevInstructions.txt` updated with latest real setup steps and ARNs/resource names.
3. Update this file (`MANASVI_CODEX_CONTEXT.md`) section **Session Log**.
4. Never delete previous history entries.
5. Do not break existing local app flows.
6. Run tests after code changes:
   `python -m pytest -q`

---

## Mandatory Final Artifact Package (Manasvi -> Kunal)
Share these values exactly:
1. `S3_BUCKET_DATASETS`
2. `DYNAMODB_TABLE_JOBS` (+ any additional table names)
3. `STEP_FUNCTION_ARN`
4. Glue crawler/job names
5. Athena workgroup and output S3 path
6. Lambda names/ARNs
7. QuickSight dataset/dashboard IDs
8. CloudWatch alarm names
9. IAM Access Key/Secret for Kunal (secure channel)

---

## Session Log (Manasvi's Codex Must Keep Updating)
Format:
`[YYYY-MM-DD HH:MM:SS +TZ] <action summary>`

Initial entry:
- [2026-03-10 15:10:00 +05:30] Context file created and handed over for Manasvi Codex continuity.
