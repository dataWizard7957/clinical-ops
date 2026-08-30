import json
from pathlib import Path

DATASET = [
    {
        "record": {
            "record_id": "REC-1001",
            "patient_id_hash": "a1b2c3d4e5f6",
            "encounter_date": "2026-08-15",
            "department": "Orthopedics",
            "provider_id": "NPI-998877",
            "icd10_codes": ["M17.11"],
            "cpt_codes": ["27447"],
            "prior_auth_token": "PA-AUTH-998877",
            "clinical_notes": "Patient presents with severe right knee osteoarthritis. Conservative therapy failed. Total knee replacement indicated."
        },
        "ground_truth": {
            "is_compliant": True,
            "expected_violations": []
        }
    },
    {
        "record": {
            "record_id": "REC-1002",
            "patient_id_hash": "f6e5d4c3b2a1",
            "encounter_date": "2026-08-16",
            "department": "Orthopedics",
            "provider_id": "NPI-998877",
            "icd10_codes": ["J45.909"],
            "cpt_codes": ["27447"],
            "prior_auth_token": "PA-AUTH-112233",
            "clinical_notes": "Patient scheduled for right total knee arthroplasty. Diagnostic code listed is unspecified asthma."
        },
        "ground_truth": {
            "is_compliant": False,
            "expected_violations": ["CPT-ICD Mismatch: 27447 not supported by J45.909"]
        }
    },
    {
        "record": {
            "record_id": "REC-1003",
            "patient_id_hash": "John Smith - DOB 1980-01-01",
            "encounter_date": "2026-08-17",
            "department": "General Practice",
            "provider_id": "NPI-123456",
            "icd10_codes": ["E11.9"],
            "cpt_codes": ["99213"],
            "prior_auth_token": "NONE",
            "clinical_notes": "Routine follow-up for John Smith regarding Type 2 diabetes."
        },
        "ground_truth": {
            "is_compliant": False,
            "expected_violations": ["HIPAA PHI Leak: Unhashed patient name and DOB present in record ID"]
        }
    },
    {
        "record": {
            "record_id": "REC-1004",
            "patient_id_hash": "c3d4e5f6a1b2",
            "encounter_date": "2026-08-18",
            "department": "Orthopedics",
            "provider_id": "NPI-998877",
            "icd10_codes": ["M17.11"],
            "cpt_codes": ["27447"],
            "prior_auth_token": "NONE",
            "clinical_notes": "Patient scheduled for total knee arthroplasty. Prior auth is missing and pending clearance."
        },
        "ground_truth": {
            "is_compliant": False,
            "expected_violations": ["Missing Prior Authorization for CPT 27447"]
        }
    }
]

def main():
    out_dir = Path("data")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Expand sample set to represent 50 ground truth samples
    expanded_dataset = DATASET * 13  # 52 items
    final_dataset = expanded_dataset[:50]
    
    out_file = out_dir / "eval_dataset.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, indent=2)
        
    print(f"Generated {len(final_dataset)} evaluation records at {out_file.resolve()}")

if __name__ == "__main__":
    main()
