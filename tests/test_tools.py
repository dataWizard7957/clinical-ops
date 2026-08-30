from dataclasses import dataclass
import pytest

from src.agent.dependencies import AuditDependencies
from src.agent.system import verify_icd10, check_cpt_icd_mismatch
from src.agent.schemas import AuditReport, ComplianceViolation


@dataclass
class MockContext:
    deps: AuditDependencies


@pytest.fixture
def audit_deps():
    return AuditDependencies()


def test_verify_icd10_valid(audit_deps):
    ctx = MockContext(deps=audit_deps)
    assert verify_icd10(ctx, "M17.11") is True
    assert verify_icd10(ctx, " m17.11 ") is True
    assert verify_icd10(ctx, "E11.9") is True


def test_verify_icd10_invalid(audit_deps):
    ctx = MockContext(deps=audit_deps)
    assert verify_icd10(ctx, "INVALID_CODE_999") is False
    assert verify_icd10(ctx, "X99.99") is False


def test_check_cpt_icd_mismatch_supported(audit_deps):
    ctx = MockContext(deps=audit_deps)
    result = check_cpt_icd_mismatch(ctx, cpt_code="27447", icd10_codes=["M17.11"])
    assert result["valid"] is True
    assert "clinically supported" in result["message"]


def test_check_cpt_icd_mismatch_unsupported(audit_deps):
    ctx = MockContext(deps=audit_deps)
    result = check_cpt_icd_mismatch(ctx, cpt_code="27447", icd10_codes=["J45.909"])
    assert result["valid"] is False
    assert "requires one of" in result["message"]


def test_audit_report_schema_parsing():
    violation = ComplianceViolation(
        rule_id="RULE-AUTH-01",
        severity="CRITICAL",
        description="Missing prior authorization for restricted CPT code 27447.",
        evidence_quote="Prior Auth Token: NONE",
        remediation_step="Obtain retroactive authorization or submit appeal."
    )
    
    report = AuditReport(
        record_id="REC-1001",
        overall_compliant=False,
        confidence_score=0.95,
        human_in_the_loop_required=False,
        violations=[violation]
    )

    assert report.record_id == "REC-1001"
    assert report.overall_compliant is False
    assert len(report.violations) == 1
    assert report.violations[0].severity == "CRITICAL"
