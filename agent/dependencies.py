from dataclasses import dataclass, field
from typing import Set, Dict


@dataclass
class AuditDependencies:
    """
    Runtime context and reference registries injected into Pydantic AI tools.
    """
    # Ground-truth ICD-10 registry subset for clinical validation
    valid_icd10_codes: Set[str] = field(
        default_factory=lambda: {
            "M17.11", "M17.12", "E11.9", "I10", "J45.909", 
            "G43.909", "M54.50", "Z00.00", "K21.9", "F41.1"
        }
    )

    # Compatible ICD-10 to CPT mappings for clinical indication verification
    cpt_icd_matrix: Dict[str, Set[str]] = field(
        default_factory=lambda: {
            "27447": {"M17.11", "M17.12"},  # Total knee arthroplasty requires knee osteoarthritis
            "99213": {"E11.9", "I10", "J45.909", "K21.9", "F41.1"}, # Mid-level outpatient visit
            "99214": {"E11.9", "I10", "M54.50"},
            "72148": {"M54.50"},            # Lumbar MRI requires lumbar pain diagnosis
        }
    )
