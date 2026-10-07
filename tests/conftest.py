import json
import os

# Direct-mode tests load the GenLayer SDK from this GenVM release, matching
# the `py-genlayer:latest` runner that Studio resolves the contract header to.
os.environ.setdefault("GENVM_VERSION", "v0.6.0-rc8")

import pytest
from gltest.direct import wasi_mock


@pytest.fixture(autouse=True)
def json_llm_mocks_as_text(monkeypatch):
    # gltest 0.30.0rc2 hands mocked JSON responses to the contract as a dict,
    # while the GenVM v0.6 SDK decodes `response_format="json"` from raw text.
    original = wasi_mock._handle_llm_request

    def handle(vm, data):
        result = original(vm, data)
        if data.get("response_format") == "json" and not isinstance(result.get("ok"), str):
            result = {"ok": json.dumps(result["ok"])}
        return result

    monkeypatch.setattr(wasi_mock, "_handle_llm_request", handle)
