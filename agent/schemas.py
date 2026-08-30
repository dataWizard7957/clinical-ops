from typing import List
from pydantic import BaseModel, Field


class ComplianceViolation(BaseModel):
    rule_id: str = Field(description="Standardized code for the violated rule (e.g., RULE-HIPAA-01)")
    severity: str = Field(description="Severity classification: CRITICAL, HIGH, MEDIUM, LOW")
    description: str = Field(description="Concise description of why this constitutes a violation")
    evidence_quote: str = Field(description="Exact snippet or reference from record backing the violation")
    remediation_step: str = Field(description="Actionable step required to fix or mitigate the issue")


class AuditReport(BaseModel):
    record_id: str = Field(description="Unique record identifier audited")
    overall_compliant: bool = Field(description="True if zero critical/high violations are found")
    confidence_score: float = Field(description="Confidence score from 0.0 to 1.0 in the audit output")
    human_in_the_loop_required: bool = Field(description="Flags if low confidence or ambiguity requires human review")
    violations: List[ComplianceViolation] = Field(default_factory=list)
