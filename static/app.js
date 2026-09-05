function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

const askBtn = document.getElementById("ask-btn");
const resultEl = document.getElementById("result");
const questionEl = document.getElementById("question");
const strategyEl = document.getElementById("strategy");
const regionEl = document.getElementById("region");
const retrievalModeEl = document.getElementById("retrieval-mode");

async function ask() {
  const question = questionEl.value.trim();
  if (!question) return;

  askBtn.disabled = true;
  resultEl.innerHTML = `<div class="panel"><span class="spinner"></span>Reading the addenda…</div>`;

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        strategy: strategyEl.value,
        region: regionEl.value || null,
        retrieval_mode: retrievalModeEl.value,
      }),
    });
    const data = await res.json();
    render(data);
  } catch (err) {
    resultEl.innerHTML = `<div class="panel">Request failed: ${escapeHtml(String(err))}</div>`;
  } finally {
    askBtn.disabled = false;
  }
}

const REFUSAL_REASONS = {
  low_retrieval_confidence: "None of the six addenda scored high enough to trust as a source.",
  model_declined: "A source was retrieved, but it didn't actually answer the question.",
  unverifiable_citation: "The draft answer's citation couldn't be traced back to a real clause.",
};

function render(data) {
  if (data.refused) {
    const reasonText = REFUSAL_REASONS[data.reason] || "The corpus doesn't support a grounded answer here.";
    resultEl.innerHTML = `
      <div class="panel">
        <span class="badge refuse">Refused</span>
        <div class="answer-text">${escapeHtml(reasonText)}</div>
        <div class="muted">${
          data.top_score != null ? `Top retrieval score: ${data.top_score.toFixed(4)}` : ""
        }</div>
      </div>`;
    return;
  }

  const chips = (data.citations || [])
    .map(
      (c) =>
        `<span class="citation-chip">${escapeHtml(c.chunk_id)} — ${escapeHtml(c.policy_id)}${
          c.section ? " §" + escapeHtml(c.section) : ""
        }</span>`
    )
    .join("");

  resultEl.innerHTML = `
    <div class="panel">
      <span class="badge ok">Answered</span>
      <div class="answer-text">${escapeHtml(data.answer || "")}</div>
      <div class="citations">${chips}</div>
    </div>`;
}

askBtn.addEventListener("click", ask);
questionEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) ask();
});
