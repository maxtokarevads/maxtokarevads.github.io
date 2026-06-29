"""
Web dashboard for the AI Marketing Agent.
Run: python web_dashboard.py
Open: http://localhost:5000
"""
import json
import os
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Marketing Agent</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f1117; color: #e2e8f0; min-height: 100vh; }
  header { background: #1a1d2e; border-bottom: 1px solid #2d3748; padding: 16px 24px;
           display: flex; align-items: center; gap: 12px; }
  header h1 { font-size: 18px; font-weight: 600; color: #60a5fa; }
  header span { font-size: 13px; color: #64748b; }
  .layout { display: grid; grid-template-columns: 360px 1fr; height: calc(100vh - 57px); }
  .sidebar { background: #1a1d2e; border-right: 1px solid #2d3748;
             padding: 20px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; }
  .main { padding: 20px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; }
  label { font-size: 12px; color: #94a3b8; font-weight: 500; text-transform: uppercase;
          letter-spacing: .05em; display: block; margin-bottom: 6px; }
  select, textarea { width: 100%; background: #0f1117; border: 1px solid #2d3748;
                     color: #e2e8f0; border-radius: 6px; padding: 8px 10px; font-size: 13px; }
  select:focus, textarea:focus { outline: none; border-color: #2563eb; }
  textarea { resize: vertical; font-family: 'JetBrains Mono', 'Fira Code', monospace;
             font-size: 12px; line-height: 1.5; }
  button#run-btn { background: #2563eb; color: #fff; border: none; border-radius: 6px;
                   padding: 10px 0; font-size: 14px; font-weight: 600; cursor: pointer;
                   transition: background .15s; }
  button#run-btn:hover { background: #1d4ed8; }
  button#run-btn:disabled { background: #1e3a8a; color: #93c5fd; cursor: not-allowed; }
  .card { background: #1a1d2e; border: 1px solid #2d3748; border-radius: 8px;
          padding: 16px; }
  .card-title { font-size: 12px; color: #94a3b8; font-weight: 600; text-transform: uppercase;
                letter-spacing: .05em; margin-bottom: 12px; }
  pre#result { white-space: pre-wrap; word-break: break-word; font-family: inherit;
               font-size: 13px; line-height: 1.65; color: #e2e8f0; min-height: 120px; }
  .meta-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
  .badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: 500; }
  .badge-mode { background: #1e3a5f; color: #60a5fa; }
  .badge-platform { background: #1a3a2a; color: #34d399; }
  .badge-agent { background: #172554; color: #93c5fd; }
  .spinner { display: none; width: 16px; height: 16px; border: 2px solid #1e3a8a;
             border-top-color: #60a5fa; border-radius: 50%; animation: spin .6s linear infinite;
             margin: 0 auto; }
  @keyframes spin { to { transform: rotate(360deg); } }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th { text-align: left; padding: 6px 8px; color: #64748b; font-weight: 500;
       border-bottom: 1px solid #2d3748; }
  td { padding: 6px 8px; border-bottom: 1px solid #1e2536; color: #94a3b8; }
  td:first-child { color: #e2e8f0; }
  .cache-hit { color: #34d399; font-weight: 600; }
  .err { color: #f87171; }
  #error-box { display: none; background: #2d1515; border: 1px solid #7f1d1d;
               border-radius: 6px; padding: 12px; color: #fca5a5; font-size: 13px; }
</style>
</head>
<body>
<header>
  <h1>AI Marketing Agent</h1>
  <span>Google · Meta · TikTok</span>
</header>
<div class="layout">
  <!-- Sidebar: controls -->
  <div class="sidebar">
    <div>
      <label>Agent</label>
      <select id="agent">
        <option value="ads">ads</option>
        <option value="seo">seo</option>
        <option value="strategy">strategy</option>
        <option value="creative">creative</option>
      </select>
    </div>
    <div>
      <label>Platform</label>
      <select id="platform">
        <option value="meta">meta</option>
        <option value="google">google</option>
        <option value="tiktok">tiktok</option>
        <option value="">(none)</option>
      </select>
    </div>
    <div>
      <label>Mode</label>
      <select id="mode">
        <option value="analyze">analyze</option>
        <option value="plan">plan</option>
        <option value="copy">copy</option>
        <option value="audit">audit</option>
        <option value="retargeting">retargeting</option>
        <option value="ab_test">ab_test</option>
        <option value="budget">budget</option>
        <option value="research">research</option>
        <option value="landing">landing</option>
        <option value="forecast">forecast</option>
      </select>
    </div>
    <div>
      <label>Payload (JSON fields to merge)</label>
      <textarea id="payload" rows="10">{
  "product": "SaaS CRM",
  "metrics": {
    "ctr": 0.8,
    "frequency": 4.2,
    "hook_rate": 18,
    "roas": 1.9
  }
}</textarea>
    </div>
    <button id="run-btn" onclick="runAgent()">Run Agent</button>
    <div class="spinner" id="spinner"></div>
    <div id="error-box"></div>
  </div>

  <!-- Main: result + usage -->
  <div class="main">
    <div class="card" id="result-card" style="display:none">
      <div class="card-title">Result</div>
      <div class="meta-row" id="meta-row"></div>
      <pre id="result"></pre>
    </div>

    <div class="card">
      <div class="card-title">Token Usage Log</div>
      <table id="usage-table">
        <thead>
          <tr>
            <th>Time</th><th>Agent</th><th>Mode</th><th>Model</th>
            <th>Input</th><th>Output</th><th>Cache read</th><th>Cache write</th>
          </tr>
        </thead>
        <tbody id="usage-body">
          <tr><td colspan="8" style="color:#4a5568;padding:12px 8px">No usage data yet.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<script>
async function runAgent() {
  const btn = document.getElementById('run-btn');
  const spinner = document.getElementById('spinner');
  const errBox = document.getElementById('error-box');
  errBox.style.display = 'none';
  btn.disabled = true;
  spinner.style.display = 'block';

  let extra = {};
  try { extra = JSON.parse(document.getElementById('payload').value || '{}'); }
  catch(e) {
    errBox.textContent = 'Invalid JSON in payload: ' + e.message;
    errBox.style.display = 'block';
    btn.disabled = false; spinner.style.display = 'none';
    return;
  }

  const body = {
    agent:    document.getElementById('agent').value,
    platform: document.getElementById('platform').value,
    mode:     document.getElementById('mode').value,
    ...extra,
  };

  try {
    const resp = await fetch('/api/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    const data = await resp.json();

    if (data.error) {
      errBox.textContent = 'Agent error: ' + data.error;
      errBox.style.display = 'block';
    } else {
      document.getElementById('result-card').style.display = 'block';
      document.getElementById('result').textContent = data.result || JSON.stringify(data, null, 2);
      const meta = document.getElementById('meta-row');
      meta.innerHTML = '';
      if (data.agent)      meta.innerHTML += `<span class="badge badge-agent">${data.agent}</span>`;
      if (data.platform)   meta.innerHTML += `<span class="badge badge-platform">${data.platform}</span>`;
      if (data.mode)       meta.innerHTML += `<span class="badge badge-mode">${data.mode}</span>`;
      if (data.model_used) meta.innerHTML += `<span class="badge" style="background:#1e2536;color:#64748b;font-size:10px">${data.model_used.replace('claude-','')}</span>`;
    }
  } catch(e) {
    errBox.textContent = 'Request failed: ' + e.message;
    errBox.style.display = 'block';
  }

  btn.disabled = false;
  spinner.style.display = 'none';
  loadUsage();
}

async function loadUsage() {
  const resp = await fetch('/api/usage');
  const rows = await resp.json();
  const tbody = document.getElementById('usage-body');
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="8" style="color:#4a5568;padding:12px 8px">No usage data yet.</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(r => {
    const cacheRead  = r.cache_read  || 0;
    const cacheWrite = r.cache_write || 0;
    const readCell   = cacheRead ? `<td class="cache-hit">+${cacheRead}</td>` : '<td>—</td>';
    const writeCell  = cacheWrite ? `<td style="color:#fb923c">${cacheWrite}</td>` : '<td>—</td>';
    const ts = r.ts ? r.ts.substring(11, 19) : '';
    return `<tr>
      <td>${ts}</td>
      <td>${r.agent||'—'}</td>
      <td>${r.mode||'—'}</td>
      <td style="color:#64748b;font-size:11px">${(r.model||'').replace('claude-','')}</td>
      <td>${r.input_tokens||0}</td>
      <td>${r.output_tokens||0}</td>
      ${readCell}${writeCell}
    </tr>`;
  }).join('');
}

loadUsage();
setInterval(loadUsage, 10000);
</script>
</body>
</html>"""


_analyzer = None
_manager  = None
_init_lock = __import__("threading").Lock()


def _get_manager():
    global _analyzer, _manager
    if _manager is None:
        with _init_lock:
            if _manager is None:
                from claude_http_analyzer import ClaudeHTTPAnalyzer
                from agents.manager import AgentsManager
                _analyzer = ClaudeHTTPAnalyzer()
                _manager  = AgentsManager(_analyzer)
    return _manager


@app.route("/")
def index():
    return render_template_string(_HTML)


@app.route("/api/run", methods=["POST"])
def api_run():
    try:
        payload    = request.get_json(force=True) or {}
        agent_type = payload.pop("agent", "ads")
        result     = _get_manager().run(agent_type, payload)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/usage")
def api_usage():
    try:
        import storage
        storage.init_db()
        return jsonify(storage.get_usage_summary(limit=50))
    except Exception as exc:
        return jsonify([])


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import storage
    storage.init_db()
    port = int(os.getenv("DASHBOARD_PORT", 5000))
    print(f"Dashboard: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
