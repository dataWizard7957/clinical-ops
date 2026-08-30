import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Load .env variables automatically
load_dotenv(ROOT_DIR / ".env")

from src.baseline.simple_solver import run_baseline_audit
from src.agent.system import audit_agent
from src.agent.dependencies import AuditDependencies
from src.agent.schemas import AuditReport


class EvalMetrics(BaseModel):
    total_samples: int = 0
    schema_failures: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    true_negatives: int = 0

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return round(self.true_positives / denom, 4) if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return round(self.true_positives / denom, 4) if denom > 0 else 0.0

    @property
    def schema_success_rate(self) -> float:
        if self.total_samples == 0:
            return 0.0
        return round((self.total_samples - self.schema_failures) / self.total_samples * 100, 2)


# Retry wrapper for rate limits / API errors with exponential backoff
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: print(
        f" [Rate Limit / API Error] Retrying in {retry_state.next_action.sleep:.1f}s..."
    ),
)
def safe_run_baseline(rec: Dict[str, Any]):
    return run_baseline_audit(rec)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: print(
        f" [Rate Limit / API Error] Retrying in {retry_state.next_action.sleep:.1f}s..."
    ),
)
def safe_run_agent(prompt: str, deps: AuditDependencies):
    return audit_agent.run_sync(prompt, deps=deps)


def evaluate_baseline(dataset: List[Dict[str, Any]]) -> EvalMetrics:
    metrics = EvalMetrics(total_samples=len(dataset))

    for idx, item in enumerate(dataset):
        rec = item["record"]
        gt = item["ground_truth"]
        
        try:
            result, schema_valid = safe_run_baseline(rec)
            if not schema_valid:
                metrics.schema_failures += 1

            agent_detected_non_compliant = not result.get("overall_compliant", True)
            gt_is_non_compliant = not gt["is_compliant"]

            if gt_is_non_compliant and agent_detected_non_compliant:
                metrics.true_positives += 1
            elif not gt_is_non_compliant and agent_detected_non_compliant:
                metrics.false_positives += 1
            elif gt_is_non_compliant and not agent_detected_non_compliant:
                metrics.false_negatives += 1
            else:
                metrics.true_negatives += 1

        except Exception as e:
            print(f"[Record {rec.get('record_id')}] Baseline Execution Error: {e}")
            metrics.schema_failures += 1
            metrics.false_negatives += 1

        # Pause to throttle requests and respect Groq 8000 TPM limit
        time.sleep(15.0)

    return metrics


def evaluate_agent(dataset: List[Dict[str, Any]]) -> EvalMetrics:
    metrics = EvalMetrics(total_samples=len(dataset))
    deps = AuditDependencies()

    for idx, item in enumerate(dataset):
        rec = item["record"]
        gt = item["ground_truth"]

        prompt = f"""
        Perform a clinical compliance audit on the following record:
        Record ID: {rec.get('record_id')}
        Patient Hash/ID: {rec.get('patient_id_hash')}
        Encounter Date: {rec.get('encounter_date')}
        Department: {rec.get('department')}
        Provider ID: {rec.get('provider_id')}
        ICD-10 Codes: {rec.get('icd10_codes')}
        CPT Codes: {rec.get('cpt_codes')}
        Prior Auth Token: {rec.get('prior_auth_token')}
        Clinical Notes: {rec.get('clinical_notes')}
        """

        try:
            run_result = safe_run_agent(prompt, deps)
            
            # Pydantic AI output accessor fallback (output vs data)
            if hasattr(run_result, "output"):
                report: AuditReport = run_result.output
            else:
                report: AuditReport = run_result.data
            
            agent_detected_non_compliant = not report.overall_compliant
            gt_is_non_compliant = not gt["is_compliant"]

            if gt_is_non_compliant and agent_detected_non_compliant:
                metrics.true_positives += 1
            elif not gt_is_non_compliant and agent_detected_non_compliant:
                metrics.false_positives += 1
            elif gt_is_non_compliant and not agent_detected_non_compliant:
                metrics.false_negatives += 1
            else:
                metrics.true_negatives += 1

        except Exception as e:
            print(f"[Record {rec.get('record_id')}] Agent Error: {e}")
            metrics.schema_failures += 1
            metrics.false_negatives += 1

        # Pause to throttle requests and respect Groq 8000 TPM limit
        time.sleep(3.0)

    return metrics


def main():
    dataset_path = ROOT_DIR / "data" / "eval_dataset.json"
    if not dataset_path.exists():
        print(f"Error: Dataset not found at {dataset_path}. Run scripts/generate_dataset.py first.")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # Slice to 20 samples for faster local iteration
    dataset = dataset[:20]

    print(f"Running Evaluation Benchmark over {len(dataset)} records...")
    print("---------------------------------------------------------")

    print("\n[1/2] Evaluating Single-Prompt Baseline...")
    baseline_metrics = evaluate_baseline(dataset)

    print("\n[2/2] Evaluating Pydantic AI Compliance Agent...")
    agent_metrics = evaluate_agent(dataset)

    print("\n=========================================================")
    print("               BENCHMARK EVALUATION RESULTS              ")
    print("=========================================================")
    print(f"{'Metric':<30} | {'Baseline':<12} | {'Pydantic AI Agent':<15}")
    print("-" * 65)
    print(f"{'Schema Success Rate':<30} | {str(baseline_metrics.schema_success_rate)+'%':<12} | {str(agent_metrics.schema_success_rate)+'%':<15}")
    print(f"{'Precision (Violation Detection)':<30} | {baseline_metrics.precision:<12} | {agent_metrics.precision:<15}")
    print(f"{'Recall (Violation Detection)':<30} | {baseline_metrics.recall:<12} | {agent_metrics.recall:<15}")
    print(f"{'True Positives':<30} | {baseline_metrics.true_positives:<12} | {agent_metrics.true_positives:<15}")
    print(f"{'False Positives':<30} | {baseline_metrics.false_positives:<12} | {agent_metrics.false_positives:<15}")
    print(f"{'False Negatives':<30} | {baseline_metrics.false_negatives:<12} | {agent_metrics.false_negatives:<15}")
    print("=========================================================")


if __name__ == "__main__":
    main()
