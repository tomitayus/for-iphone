#!/usr/bin/env python3
"""
Web API server for Multi-AI Diagram Automation.
Allows iPhone (via iOS Shortcuts) to submit questions and retrieve diagrams.

Usage:
  python3 server.py
  python3 server.py --port 8080
  python3 server.py --host 0.0.0.0  # Allow external access
"""

import argparse
import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.ai_clients import ask_all
from src.synthesizer import synthesize
from src.renderer import render_html

# ── App ────────────────────────────────────────────────────────────

app = FastAPI(
    title="Multi-AI Diagram API",
    description="4つのAIに質問を並列送信し、統合HTML図解を生成",
)

# In-memory job store
jobs: dict[str, dict] = {}

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Models ─────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    job_id: str
    status: str  # "processing" | "completed" | "error"
    question: str
    created_at: str
    completed_at: str | None = None
    diagram_url: str | None = None
    ai_results: list[dict] | None = None
    error: str | None = None


# ── Background processing ──────────────────────────────────────────

async def _process_job(job_id: str, question: str):
    """Run the full pipeline in the background."""
    job = jobs[job_id]

    try:
        # Step 1: Ask all AIs
        job["status"] = "asking_ais"
        result = await ask_all(question)

        job["ai_results"] = [
            {
                "provider": r.provider,
                "model": r.model,
                "elapsed_sec": r.elapsed_sec,
                "error": r.error,
                "content_length": len(r.content),
            }
            for r in result.responses
        ]

        # Step 2: Synthesize with Claude
        job["status"] = "synthesizing"
        html_content = await synthesize(result)

        # Step 3: Save HTML
        job["status"] = "saving"
        html_path = render_html(result, html_content)
        filename = Path(html_path).name

        job["status"] = "completed"
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
        job["filename"] = filename
        job["diagram_url"] = f"/diagrams/{filename}"

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        job["completed_at"] = datetime.now(timezone.utc).isoformat()


# ── Endpoints ──────────────────────────────────────────────────────

@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """質問を送信してジョブを開始する。"""
    if not req.question.strip():
        raise HTTPException(400, "question is required")

    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "question": req.question,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "filename": None,
        "diagram_url": None,
        "ai_results": None,
        "error": None,
    }

    asyncio.create_task(_process_job(job_id, req.question))

    return AskResponse(
        job_id=job_id,
        status="queued",
        message="Processing started. Poll GET /jobs/{job_id} for status.",
    )


@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job(job_id: str):
    """ジョブの状態を確認する。"""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    return JobStatus(**job)


@app.get("/jobs")
async def list_jobs():
    """最近のジョブ一覧を返す（最新20件）。"""
    sorted_jobs = sorted(jobs.values(), key=lambda j: j["created_at"], reverse=True)
    return [
        {
            "job_id": j["job_id"],
            "status": j["status"],
            "question": j["question"][:80],
            "created_at": j["created_at"],
            "diagram_url": j["diagram_url"],
        }
        for j in sorted_jobs[:20]
    ]


@app.get("/diagrams/{filename}")
async def get_diagram(filename: str):
    """生成されたHTML図解を返す。"""
    filepath = Path(OUTPUT_DIR) / filename
    if not filepath.exists():
        raise HTTPException(404, "Diagram not found")
    return FileResponse(filepath, media_type="text/html")


@app.post("/ask/sync")
async def ask_sync(req: AskRequest):
    """
    同期版: 質問を送信し、完了まで待ってから結果を返す。
    iOS ショートカットで1回のリクエストで完結させたい場合に使用。
    タイムアウトに注意（処理に30〜120秒かかる場合あり）。
    """
    if not req.question.strip():
        raise HTTPException(400, "question is required")

    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "question": req.question,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "filename": None,
        "diagram_url": None,
        "ai_results": None,
        "error": None,
    }

    await _process_job(job_id, req.question)

    job = jobs[job_id]
    if job["status"] == "error":
        raise HTTPException(500, job["error"])

    return {
        "job_id": job_id,
        "status": "completed",
        "question": req.question,
        "diagram_url": job["diagram_url"],
        "ai_results": job["ai_results"],
    }


@app.get("/", response_class=HTMLResponse)
async def index():
    """簡易Web UI。"""
    return """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Multi-AI Diagram</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0a0a1a; color: #e0e0e0;
    min-height: 100vh; display: flex; flex-direction: column; align-items: center;
    padding: 40px 16px;
  }
  h1 { font-size: 1.5rem; margin-bottom: 8px; }
  .subtitle { color: #888; font-size: 0.9rem; margin-bottom: 32px; }
  form {
    width: 100%; max-width: 600px;
    display: flex; gap: 8px; margin-bottom: 32px;
  }
  input[type=text] {
    flex: 1; padding: 12px 16px; border-radius: 12px;
    border: 1px solid #333; background: #1a1a2e; color: #e0e0e0;
    font-size: 1rem; outline: none;
  }
  input[type=text]:focus { border-color: #3b82f6; }
  button {
    padding: 12px 24px; border-radius: 12px; border: none;
    background: #3b82f6; color: white; font-size: 1rem;
    font-weight: 600; cursor: pointer;
  }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
  #status {
    width: 100%; max-width: 600px;
    padding: 16px; border-radius: 12px;
    background: #1a1a2e; display: none;
  }
  #status.show { display: block; }
  .step { padding: 4px 0; color: #aaa; }
  .step.active { color: #22c55e; }
  .step.error { color: #ef4444; }
  a { color: #3b82f6; text-decoration: none; }
  a:hover { text-decoration: underline; }
  #history { width: 100%; max-width: 600px; margin-top: 24px; }
  #history h2 { font-size: 1.1rem; margin-bottom: 12px; color: #888; }
  .job-item {
    padding: 12px; border-radius: 8px; background: #1a1a2e;
    margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;
  }
  .job-q { font-size: 0.9rem; flex: 1; }
  .badge {
    font-size: 0.75rem; padding: 2px 8px; border-radius: 4px;
    background: #22c55e33; color: #22c55e; margin-left: 8px; white-space: nowrap;
  }
  .badge.processing { background: #f59e0b33; color: #f59e0b; }
</style>
</head>
<body>
<h1>Multi-AI Diagram</h1>
<p class="subtitle">4つのAIに同じ質問を投げて統合図解を生成</p>

<form id="askForm">
  <input type="text" id="questionInput" placeholder="質問を入力..." autofocus>
  <button type="submit" id="submitBtn">送信</button>
</form>

<div id="status">
  <div class="step" id="s1">1. 4つのAIに質問中...</div>
  <div class="step" id="s2">2. Claude で統合分析中...</div>
  <div class="step" id="s3">3. HTML図解を生成中...</div>
  <div class="step" id="s4">4. 完了!</div>
  <div id="resultLink" style="margin-top:12px"></div>
</div>

<div id="history"><h2>履歴</h2><div id="jobList"></div></div>

<script>
const form = document.getElementById('askForm');
const input = document.getElementById('questionInput');
const btn = document.getElementById('submitBtn');
const status = document.getElementById('status');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (!q) return;

  btn.disabled = true;
  status.className = 'show';
  document.querySelectorAll('.step').forEach(s => s.className = 'step');
  document.getElementById('resultLink').innerHTML = '';
  document.getElementById('s1').classList.add('active');

  try {
    const res = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q }),
    });
    const data = await res.json();
    pollJob(data.job_id);
  } catch (err) {
    document.getElementById('s1').classList.replace('active', 'error');
    document.getElementById('s1').textContent = 'Error: ' + err.message;
    btn.disabled = false;
  }
});

async function pollJob(jobId) {
  const poll = setInterval(async () => {
    try {
      const res = await fetch('/jobs/' + jobId);
      const job = await res.json();

      document.querySelectorAll('.step').forEach(s => s.className = 'step');

      if (job.status === 'asking_ais' || job.status === 'queued') {
        document.getElementById('s1').classList.add('active');
      } else if (job.status === 'synthesizing') {
        document.getElementById('s1').classList.add('active');
        document.getElementById('s2').classList.add('active');
      } else if (job.status === 'saving') {
        document.getElementById('s1').classList.add('active');
        document.getElementById('s2').classList.add('active');
        document.getElementById('s3').classList.add('active');
      } else if (job.status === 'completed') {
        clearInterval(poll);
        document.querySelectorAll('.step').forEach(s => s.classList.add('active'));
        document.getElementById('resultLink').innerHTML =
          '<a href="' + job.diagram_url + '" target="_blank">📊 図解を開く</a>';
        btn.disabled = false;
        input.value = '';
        loadHistory();
      } else if (job.status === 'error') {
        clearInterval(poll);
        document.getElementById('s4').textContent = 'Error: ' + job.error;
        document.getElementById('s4').classList.add('error');
        btn.disabled = false;
      }
    } catch (e) {
      clearInterval(poll);
      btn.disabled = false;
    }
  }, 2000);
}

async function loadHistory() {
  try {
    const res = await fetch('/jobs');
    const list = await res.json();
    const el = document.getElementById('jobList');
    el.innerHTML = list.map(j => `
      <div class="job-item">
        <span class="job-q">${j.question}</span>
        ${j.diagram_url
          ? '<a href="' + j.diagram_url + '">開く</a>'
          : '<span class="badge processing">' + j.status + '</span>'}
      </div>
    `).join('');
  } catch (e) {}
}
loadHistory();
</script>
</body>
</html>
"""


# ── Server startup ─────────────────────────────────────────────────

def start_server(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn

    print(f"\n{'='*50}")
    print(f"  Multi-AI Diagram API Server")
    print(f"  http://{host}:{port}")
    print(f"{'='*50}")
    print(f"\n  Endpoints:")
    print(f"    GET  /             Web UI")
    print(f"    POST /ask          非同期で質問を送信")
    print(f"    POST /ask/sync     同期で質問を送信（完了まで待つ）")
    print(f"    GET  /jobs         ジョブ一覧")
    print(f"    GET  /jobs/{{id}}    ジョブ状態確認")
    print(f"    GET  /diagrams/{{f}} 図解HTMLを取得")
    print(f"\n  iOS Shortcut:")
    print(f"    POST http://<your-ip>:{port}/ask/sync")
    print(f"    Body: {{\"question\": \"あなたの質問\"}}")
    print(f"{'='*50}\n")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-AI Diagram API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    args = parser.parse_args()
    start_server(args.host, args.port)
