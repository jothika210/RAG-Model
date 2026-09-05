function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s == null ? "" : String(s);
  return div.innerHTML;
}

const runBtn = document.getElementById("run-btn");
const loadBtn = document.getElementById("load-btn");
const output = document.getElementById("output");

async function runEvaluation() {
  runBtn.disabled = true;
  loadBtn.disabled = true;
  output.innerHTML = `<div class="panel"><span class="spinner"></span>Running the full evaluation…</div>`;
  try {
    const res = await fetch("/api/admin/evaluate", { method: "POST" });
    const data = await res.json();
    renderSummary(data);
  } catch (err) {
    output.innerHTML = `<div class="panel">Request failed: ${escapeHtml(err)}</div>`;
  } finally {
    runBtn.disabled = false;
    loadBtn.disabled = false;
  }
}

async function loadLatest() {
  runBtn.disabled = true;
  loadBtn.disabled = true;
  output.innerHTML = `<div class="panel"><span class="spinner"></span>Loading the last run…</div>`;
  try {
    const res = await fetch("/api/admin/evaluate/latest");
    if (!res.ok) {
      output.innerHTML = `<div class="panel muted">No evaluation has been run yet.</div>`;
      return;
    }
    const data = await res.json();
    renderSummary({
      hit_rate_totals: data.hit_rate.totals,
      filter_demo_top1_changed: data.filter_demo.top1_changed,
      cited_answers: data.cited_answers,
      refusals: data.refusals,
    });
  } catch (err) {
    output.innerHTML = `<div class="panel">Request failed: ${escapeHtml(err)}</div>`;
  } finally {
    runBtn.disabled = false;
    loadBtn.disabled = false;
  }
}

function sectionHeading(text) {
  return `<h2 style="font-family:var(--font-display);font-size:1.05rem;font-weight:600;margin:0 0 0.9rem">${escapeHtml(text)}</h2>`;
}

function renderSummary(data) {
  const totals = data.hit_rate_totals || {};
  let html = `
    <div class="panel">
      ${sectionHeading("Hit-in-top-5")}
      <div class="table-wrap">
        <table>
          <tr><th>Chunking strategy</th><th class="num">Score</th></tr>
          <tr><td>Naive</td><td class="num">${escapeHtml(totals.naive)}</td></tr>
          <tr><td>Structure-aware</td><td class="num">${escapeHtml(totals.structure_aware)}</td></tr>
        </table>
      </div>
      <p class="muted" style="margin-top:0.9rem">Region filter demo changed the top-1 result: <strong style="color:var(--ink)">${
        data.filter_demo_top1_changed
      }</strong></p>
      <p class="muted" style="margin:0.25rem 0 0">Full detail lives in <code>results.md</code> and <code>data/eval_raw_dump.json</code>.</p>
    </div>
  `;

  html += `<div class="panel">${sectionHeading("Cited answers")}`;
  for (const c of data.cited_answers || []) {
    html += `
      <div style="margin-bottom:1.1rem">
        <div><strong>${escapeHtml(c.id)}</strong> · ${escapeHtml(c.question)}</div>
        ${
          c.refused
            ? `<span class="badge refuse" style="margin-top:0.5rem">Refused</span>`
            : `<div class="answer-text">${escapeHtml(c.answer)}</div>
               <div class="citations">${(c.citations || [])
                 .map((ct) => `<span class="citation-chip">${escapeHtml(ct.chunk_id)}</span>`)
                 .join("")}</div>`
        }
      </div>`;
  }
  html += `</div>`;

  html += `<div class="panel">${sectionHeading("Refusal transcripts")}`;
  for (const r of data.refusals || []) {
    html += `
      <div style="margin-bottom:0.85rem;display:flex;align-items:baseline;gap:0.6rem;flex-wrap:wrap">
        <span class="badge ${r.refused ? "refuse" : "ok"}">${r.refused ? "Refused" : "Answered"}</span>
        <strong>${escapeHtml(r.id)}</strong>
        <span class="muted">${escapeHtml(r.question)}</span>
        <span class="muted">— ${escapeHtml(r.reason)}</span>
      </div>`;
  }
  html += `</div>`;

  output.innerHTML = html;
}

runBtn.addEventListener("click", runEvaluation);
loadBtn.addEventListener("click", loadLatest);
