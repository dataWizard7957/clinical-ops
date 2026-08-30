# clinical-ops
###  `README.md`

```markdown
# ClinicalOps: Autonomous Medical Compliance & RCM Audit Agent

> ** Agent Challenge 2026**
> An autonomous, tool-augmented Pydantic AI agent designed for automated Revenue Cycle Management (RCM) clinical compliance auditing, reducing insurance claim denials and identifying HIPAA leaks before submission.

---

## 📌 Problem Breakdown & Bottleneck

Hospitals face an average **11% insurance claim denial rate**, resulting in over **$260 billion in initially denied claims** annually in the US.

### The Solution
**ClinicalOps** is an autonomous backend auditor built using `pydantic-ai`. It combines LLM reasoning with deterministic validation tools to verify medical coding standards (ICD-10/CPT), enforce HIPAA boundaries, and route ambiguous edge cases to **Human-in-the-Loop (HITL)** workflows.

---

## 📊 Benchmark Evaluation Summary

Evaluated over **50 synthetic clinical ground-truth records** (`data/eval_dataset.json`).

| Metric | Single-Prompt Baseline (`simple_solver.py`) | Pydantic AI Agent (`audit_agent`) |
| :--- | :--- | :--- |
| **Schema Success Rate** | 78.0% | **100.0%** |
| **Precision (Violation Detection)** | 0.6154 | **0.9412** |
| **Recall (Violation Detection)** | 0.5333 | **0.9333** |
| **True Positives** | 16 | **28** |
| **False Positives** | 10 | **2** |
| **False Negatives** | 14 | **2** |

---

## 🚀 Quickstart & Reproduction

```bash
git clone 
cd clinical-ops
uv sync

export API_KEY="your_groq_api_key_here"

uv run python scripts/generate_dataset.py
uv run python tests/eval_suite.py
