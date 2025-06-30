#!/usr/bin/env python3
"""
log_fixer.py

Flask UI with per-entry “Research Online” buttons, custom-fix inputs,
and numbered steps for each suggested fix.
"""
import threading
import webbrowser
import os

from flask import Flask, request, render_template_string
from dotenv import load_dotenv

from db import load_db, save_db
from analysis import analyze
from online_research import find_error_solution

# ─── App Setup ────────────────────────────────────────────────────────────────
load_dotenv()
app = Flask(__name__)
PORT = int(os.getenv("PORT", 5000))
OVERRIDES = load_db()

# ─── Templates ────────────────────────────────────────────────────────────────

TEMPLATE_INDEX = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Log Analyzer & Fixer</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
  <div class="container my-5">
    <div class="card shadow-sm">
      <div class="card-header bg-primary text-white text-center">
        <h3>Log Analyzer & Fixer</h3>
      </div>
      <div class="card-body">
        <form method="post">
          <div class="mb-3">
            <label for="log" class="form-label">Paste your data-center logs below:</label>
            <textarea name="log" id="log" class="form-control" rows="10"
                      placeholder="Enter or paste your server logs here…"></textarea>
          </div>
          <!-- Hidden field used to indicate initial analysis -->
          <input type="hidden" name="step" value="analyze">
          <button type="submit" class="btn btn-primary btn-lg w-100">Analyze Logs</button>
        </form>
      </div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

TEMPLATE_RESULT = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Analysis Results</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
  <div class="container my-5">
    <div class="card shadow-sm">
      <div class="card-header bg-success text-white">
        <h4>Detected Issues & Suggested Fixes</h4>
      </div>
      <div class="card-body">
        <form method="post">
          <!-- Preserve the log text for re-analysis or saving -->
          <textarea name="log" hidden>{{ log|e }}</textarea>

          {% for entry in analysis %}
          <div class="mb-4 border rounded p-3">
            <h5>{{ entry.issue_type }}</h5>
            <p><strong>Pattern:</strong> {{ entry.pattern }}</p>
            <p><strong>Fix:</strong> {{ entry.fix or '—none yet—' }}</p>

            {% if entry.steps %}
            <div class="mt-3">
              {% for step in entry.steps %}
              <p><strong>Step {{ loop.index }}:</strong> {{ step }}</p>
              {% endfor %}
            </div>
            {% endif %}

            {% if not entry.fix %}
            <div class="mt-3 d-flex gap-2">
              <!-- Custom-fix input -->
              <input name="newfix_{{ loop.index0 }}" class="form-control"
                     placeholder="Enter custom fix…">
              <!-- Research-online button -->
              <button name="research_idx" value="{{ loop.index0 }}"
                      class="btn btn-outline-primary">Research Online</button>
            </div>
            {% endif %}
          </div>
          {% endfor %}

          <div class="d-flex justify-content-between">
            <button type="submit" name="action" value="save" class="btn btn-success">
              Save All Custom Fixes
            </button>
            <a href="/" class="btn btn-outline-secondary">Start Over</a>
          </div>
        </form>

        {% if saved %}
        <div class="alert alert-info mt-3">
          Your fixes have been saved.
        </div>
        {% endif %}
      </div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ─── Routes ────────────────────────────────────────────────────────────────────


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        log_text = request.form.get("log", "")
        step = request.form.get("step")
        research = request.form.get("research_idx")
        action = request.form.get("action")

        # Always re-analyze the latest log text
        raw = analyze(log_text)

        # 1) Research-online button for a specific entry
        if research is not None:
            idx = int(research)
            entry = raw[idx]
            online_fix = find_error_solution(entry["pattern"])
            # Parse up to 6 bullet lines into steps
            steps = [line.lstrip("- ").strip()
                     for line in online_fix.splitlines() if line.strip()]
            entry["steps"] = steps[:6]
            entry["fix"] = "Follow the steps below:"
            # Save to overrides so next time it's known
            OVERRIDES[entry["pattern"]] = entry["fix"]
            save_db(OVERRIDES)
            return render_template_string(TEMPLATE_RESULT,
                                          analysis=raw,
                                          log=log_text,
                                          saved=False)

        # 2) Save-all-custom-fixes button
        if action == "save":
            for idx, entry in enumerate(raw):
                if not entry["fix"]:
                    custom = request.form.get(f"newfix_{idx}")
                    if custom:
                        OVERRIDES[entry["pattern"]] = custom
            save_db(OVERRIDES)
            # Apply overrides in the display
            updated = []
            for entry in raw:
                entry["fix"] = OVERRIDES.get(entry["pattern"], entry["fix"])
                # keep existing steps if any
                updated.append(entry)
            return render_template_string(TEMPLATE_RESULT,
                                          analysis=updated,
                                          log=log_text,
                                          saved=True)

        # 3) Default analyze: known fixes + placeholders for unknowns
        results = []
        for entry in raw:
            # If database or previous override has a fix, use it
            if entry["fix"]:
                results.append(entry)
            else:
                # no fix yet: clear steps for Research action
                entry["fix"] = ""
                entry["steps"] = []
                results.append(entry)
        return render_template_string(TEMPLATE_RESULT,
                                      analysis=results,
                                      log=log_text,
                                      saved=False)

    # GET request—show landing page
    return render_template_string(TEMPLATE_INDEX)

# ─── Main ──────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    threading.Timer(1.0,
                    lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    app.run(host="0.0.0.0", port=PORT)
