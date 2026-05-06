from __future__ import annotations

import json
from pathlib import Path


def test_step_function_definition_is_valid_json():
    path = Path("infra/stepfunctions/analytics_orchestrator.asl.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert "StartAt" in payload
    assert "States" in payload


def test_lambda_payload_examples_are_valid_json():
    payload_dir = Path("infra/lambda/payload_examples")
    for path in payload_dir.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)


def test_athena_query_template_exists_and_is_not_empty():
    path = Path("infra/athena/query_templates.sql")

    assert path.exists()
    assert path.read_text(encoding="utf-8").strip()
