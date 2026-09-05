function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s == null ? "" : String(s);
  return div.innerHTML;
}

const loadBtn = document.getElementById("load-btn");
const collectionEl = document.getElementById("collection");
const modeEl = document.getElementById("mode");
const kEl = document.getElementById("k");
const rowsEl = document.getElementById("rows");

async function load() {
  loadBtn.disabled = true;
  rowsEl.innerHTML = `<div class="panel"><span class="spinner"></span>Loading…</div>`;
  try {
    const params = new URLSearchParams({
      collection: collectionEl.value,
      mode: modeEl.value,
      k: kEl.value,
    });
    const res = await fetch(`/api/admin/inspect?${params}`);
    const data = await res.json();
    render(data);
  } catch (err) {
    rowsEl.innerHTML = `<div class="panel">Request failed: ${escapeHtml(err)}</div>`;
  } finally {
    loadBtn.disabled = false;
  }
}

function fetchedRowHtml(f, knownPolicyId, knownSection) {
  const isKnown = f.policy_id === knownPolicyId && f.section === knownSection;
  const rankBadges = [];
  if (f.semantic_rank != null) rankBadges.push(`sem #${f.semantic_rank}`);
  if (f.bm25_rank != null) rankBadges.push(`bm25 #${f.bm25_rank}`);
  const badgeText = rankBadges.length ? ` (${rankBadges.join(", ")})` : "";
  const scoreText = f.fused_score != null ? `fused=${f.fused_score}` : `score=${f.score}`;
  return `<div class="fetched-row${isKnown ? " is-known" : ""}">
    ${isKnown ? "✓ " : ""}${escapeHtml(f.policy_id)} §${escapeHtml(f.section)} — ${scoreText}${escapeHtml(badgeText)}
    <div class="fetched-chunk-id">${escapeHtml(f.chunk_id)}</div>
  </div>`;
}

function render(data) {
  let html = "";
  for (const row of data.rows) {
    const fetchedHtml = row.fetched.map((f) => fetchedRowHtml(f, row.known_policy_id, row.known_section)).join("");
    const answer = row.answer;
    const answerHtml = answer.refused
      ? `<span class="badge refuse">Refused</span><div class="muted" style="margin-top:0.5rem">Reason: ${escapeHtml(answer.reason)}</div>`
      : `<span class="badge ok">Answered</span>
         <div class="answer-text">${escapeHtml(answer.answer)}</div>
         <div class="citations">${answer.citations
           .map((c) => `<span class="citation-chip">${escapeHtml(c.chunk_id)}</span>`)
           .join("")}</div>`;

    const knownInFetched = row.fetched.some((f) => f.policy_id === row.known_policy_id && f.section === row.known_section);
    const label = knownInFetched ? "Known chunk retrieved" : "Known chunk missing";
    const labelClass = knownInFetched ? "ok" : "refuse";

    html += `
      <div class="panel trace-card">
        <div class="trace-head">
          <strong>${escapeHtml(row.id)}</strong>
          <span class="badge ${labelClass}">${escapeHtml(label)}</span>
        </div>
        <div class="trace-question">${escapeHtml(row.question)}
          <span class="muted"> — known answer: ${escapeHtml(row.known_policy_id)} §${escapeHtml(row.known_section)}</span>
        </div>
        <div class="trace-grid">
          <div>
            <div class="trace-col-label">Fetched (top-${data.k})</div>
            ${fetchedHtml}
          </div>
          <div>
            <div class="trace-col-label">Final answer</div>
            ${answerHtml}
          </div>
        </div>
      </div>`;
  }
  rowsEl.innerHTML = html;
}

loadBtn.addEventListener("click", load);
load();
