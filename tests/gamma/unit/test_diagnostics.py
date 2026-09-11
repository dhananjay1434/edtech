import pytest
from cde.diagnostics import Diagnostic, Evidence

def test_diagnostic_model():
    ev = Evidence(
        crop_id="crop1",
        bbox=[0.1, 0.1, 0.9, 0.9],
        observation="Some working"
    )
    diag = Diagnostic(
        schema_version="1.0",
        status="classified",
        error_class="Calculation Slip",
        confidence=0.9,
        summary="Calculated wrong",
        next_step="Check addition",
        evidence=[ev]
    )
    assert diag.status == "classified"
    assert diag.error_class == "Calculation Slip"
