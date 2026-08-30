import os
from pathlib import Path
import phoenix as px
from openinference.instrumentation.pydantic_ai import PydanticAIInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter


def setup_telemetry(
    project_name: str = "health-compliance-audit-agent",
    export_dir: str = "trajectories",
    enable_console_export: bool = False,
) -> px.Session:
    """
    Initializes Arize Phoenix local OpenTelemetry tracing and instruments Pydantic AI.
    """
    traj_path = Path(export_dir)
    traj_path.mkdir(parents=True, exist_ok=True)

    os.environ["PHOENIX_PROJECT_NAME"] = project_name
    os.environ["PHOENIX_WORKING_DIR"] = str(traj_path.resolve())

    session = px.launch_app(project_name=project_name)
    print(f"Phoenix Telemetry initialized at: {session.url}")

    PydanticAIInstrumentor().instrument()

    if enable_console_export:
        provider = trace.get_tracer_provider()
        if isinstance(provider, TracerProvider):
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    return session


def export_traces_to_file(output_filename: str = "trajectories/latest_agent_trace.json") -> None:
    """
    Exports active Phoenix trace dataframe directly to a local JSON file.
    """
    try:
        client = px.Client()
        spans_df = client.get_spans_dataframe()
        
        output_path = Path(output_filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        spans_df.to_json(output_path, orient="records", indent=2)
        print(f"Successfully exported {len(spans_df)} execution spans to {output_path.resolve()}")
    except Exception as e:
        print(f"Warning: Could not export traces to file: {e}")
