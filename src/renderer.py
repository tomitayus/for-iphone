"""
HTML renderer module.
Renders the synthesis result into a self-contained HTML diagram.
"""

import json
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .ai_clients import MultiAIResult

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def render_html(result: MultiAIResult, synthesis: dict, output_path: str | None = None) -> str:
    """Render the diagram as a standalone HTML file. Returns the output path."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    template = env.get_template("diagram.html")

    # Prepare template data
    responses_data = []
    for r in result.responses:
        responses_data.append({
            "provider": r.provider,
            "model": r.model,
            "content": r.content,
            "error": r.error or "",
            "elapsed_sec": r.elapsed_sec,
        })

    diagram_nodes = synthesis.get("diagram_nodes", [])
    diagram_edges = synthesis.get("diagram_edges", [])

    # Truncate question for title
    title = result.question[:60] + ("..." if len(result.question) > 60 else "")

    html = template.render(
        title=title,
        question=result.question,
        timestamp=result.timestamp,
        synthesis=synthesis,
        responses=responses_data,
        diagram_nodes_json=json.dumps(diagram_nodes, ensure_ascii=False),
        diagram_edges_json=json.dumps(diagram_edges, ensure_ascii=False),
    )

    # Determine output path
    if output_path is None:
        output_dir = os.environ.get("OUTPUT_DIR", "./output")
        os.makedirs(output_dir, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in result.question[:40])
        output_path = os.path.join(output_dir, f"diagram_{safe_name}_{result.timestamp[:10]}.html")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html, encoding="utf-8")

    return output_path
