import os
from typing import Dict, List, Union
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.test import TestModel

from src.agent.dependencies import AuditDependencies
from src.agent.schemas import AuditReport

SYSTEM_PROMPT = """
You are an expert autonomous Medical Compliance Auditor (APEX-ClinicalOps).
Your duty is to audit clinical records for compliance violations:
1. Invalid or unsupported ICD-10 diagnostic codes.
2. Mismatches between procedure codes (CPT) and diagnostic codes (ICD-10).
3. Missing prior authorization tokens on restricted procedures.
4. HIPAA violations (e.g., unanonymized patient names or unhashed identifiers).

Rules for auditing:
- Always use your available validation tools (`verify_icd10`, `check_cpt_icd_mismatch`) to verify codes before reaching a conclusion.
- If a record has ambiguous notes or conflicting codes, set `confidence_score` below 0.85 and mark `human_in_the_loop_required = True`.
- Produce strict, actionable violation descriptions.
"""

# Configure Google Gemini via Pydantic AI's native GoogleModel
if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
    # If using GEMINI_API_KEY, pass it or let GoogleModel pick up GOOGLE_API_KEY
    if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
    
    model = GoogleModel("gemini-3.1-pro-preview")
else:
    model = TestModel()

audit_agent = Agent[AuditDependencies, AuditReport](
    model=model,
    output_type=AuditReport,
    deps_type=AuditDependencies,
    system_prompt=SYSTEM_PROMPT,
    retries=5,
)


@audit_agent.tool
def verify_icd10(ctx: RunContext[AuditDependencies], icd10_code: str) -> bool:
    """Verifies whether a given ICD-10 code exists in the official registry."""
    clean_code = icd10_code.strip().upper()
    return clean_code in ctx.deps.valid_icd10_codes


@audit_agent.tool
def check_cpt_icd_mismatch(
    ctx: RunContext[AuditDependencies],
    cpt_code: str,
    icd10_codes: List[str],
) -> Dict[str, Union[str, bool]]:
    """Checks if a CPT procedure code is supported by diagnosed ICD-10 codes."""
    clean_cpt = cpt_code.strip()
    allowed_icds = ctx.deps.cpt_icd_matrix.get(clean_cpt)

    if allowed_icds is None:
        return {
            "valid": True,
            "message": f"CPT {clean_cpt} has no restricted ICD dependencies.",
        }

    has_match = any(code.strip().upper() in allowed_icds for code in icd10_codes)
    return {
        "valid": has_match,
        "message": (
            "CPT code is clinically supported."
            if has_match
            else f"CPT {clean_cpt} requires one of: {allowed_icds}"
        ),
    }
