/* ── DOM references ──────────────────────────────────────── */
const modelSelect = document.getElementById("model-select");
const refreshModelsBtn = document.getElementById("refresh-models-btn");
const newModelInput = document.getElementById("new-model-input");
const addModelBtn = document.getElementById("add-model-btn");
const modelStatus = document.getElementById("model-status");

const promptInput = document.getElementById("prompt-input");
const generateBtn = document.getElementById("generate-btn");
const generateLoader = document.getElementById("generate-loader");
const responseDisplay = document.getElementById("response-display");
const responseText = document.getElementById("response-text");

const loadHistoryBtn = document.getElementById("load-history-btn");
const historyList = document.getElementById("history-list");

/* ── Helpers ─────────────────────────────────────────────── */

function showStatus(msg, type = "info") {
  modelStatus.textContent = msg;
  modelStatus.className = "status " + type;
  modelStatus.hidden = false;
}

function hideStatus() {
  modelStatus.hidden = true;
}

/* ── Models ──────────────────────────────────────────────── */

async function loadModels() {
  try {
    const res = await fetch("/models");
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    modelSelect.innerHTML = "";

    if (data.models.length === 0) {
      modelSelect.innerHTML = '<option value="">No models found</option>';
      return;
    }

    data.models.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m;
      opt.textContent = m;
      modelSelect.appendChild(opt);
    });
  } catch (err) {
    modelSelect.innerHTML =
      '<option value="">Failed to load models</option>';
    console.error("loadModels error:", err);
  }
}

refreshModelsBtn.addEventListener("click", () => {
  loadModels();
});

addModelBtn.addEventListener("click", async () => {
  const name = newModelInput.value.trim();
  if (!name) return;

  addModelBtn.disabled = true;
  showStatus(`Pulling model "${name}"... this may take a while.`, "info");

  try {
    const res = await fetch("/add-model", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_name: name }),
    });

    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || res.statusText);
    }

    showStatus(`Model "${name}" added successfully!`, "success");
    newModelInput.value = "";
    await loadModels();
  } catch (err) {
    showStatus(`Failed to add model: ${err.message}`, "error");
  } finally {
    addModelBtn.disabled = false;
  }
});

/* ── Generation ──────────────────────────────────────────── */

generateBtn.addEventListener("click", async () => {
  const prompt = promptInput.value.trim();
  const model = modelSelect.value;

  if (!prompt) return alert("Please enter a prompt.");
  if (!model) return alert("Please select a model first.");

  generateBtn.disabled = true;
  generateLoader.hidden = false;
  responseDisplay.hidden = true;

  try {
    const res = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, model_name: model }),
    });

    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || res.statusText);
    }

    const data = await res.json();
    responseText.textContent = data.response;
    responseDisplay.hidden = false;
  } catch (err) {
    alert("Generation failed: " + err.message);
  } finally {
    generateBtn.disabled = false;
    generateLoader.hidden = true;
  }
});

/* ── History ─────────────────────────────────────────────── */

loadHistoryBtn.addEventListener("click", async () => {
  try {
    const res = await fetch("/history");
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    if (data.history.length === 0) {
      historyList.innerHTML = "<p>No history yet.</p>";
      return;
    }

    historyList.innerHTML = data.history
      .map(
        (item) => `
        <div class="history-item">
          <div class="meta">${item.model_used} &mdash; ${item.timestamp}</div>
          <div class="prompt-text">Prompt: ${escapeHtml(item.prompt)}</div>
          <div class="response-text">${escapeHtml(item.response)}</div>
        </div>`
      )
      .join("");
  } catch (err) {
    historyList.innerHTML = "<p>Failed to load history.</p>";
    console.error("history error:", err);
  }
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

/* ── Init ────────────────────────────────────────────────── */
loadModels();
