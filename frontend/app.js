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

// Map model name → type so the UI can adapt
const modelTypes = {};

async function loadModels() {
  try {
    const res = await fetch("/models");
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    modelSelect.innerHTML = "";
    Object.keys(modelTypes).forEach((k) => delete modelTypes[k]);

    if (data.models.length === 0) {
      modelSelect.innerHTML = '<option value="">No models found</option>';
      return;
    }

    data.models.forEach((m) => {
      const name = m.name || m;          // handle both object and plain string
      const type = m.type || "llm";
      const status = m.status || "online";
      modelTypes[name] = type;

      const opt = document.createElement("option");
      opt.value = name;
      if (type === "tts") {
        const tag = status === "online" ? "TTS" : "TTS - offline";
        opt.textContent = `${name}  [${tag}]`;
      } else {
        opt.textContent = name;
      }
      modelSelect.appendChild(opt);
    });

    updateGenerateUI();
  } catch (err) {
    modelSelect.innerHTML =
      '<option value="">Failed to load models</option>';
    console.error("loadModels error:", err);
  }
}

function getSelectedModelType() {
  return modelTypes[modelSelect.value] || "llm";
}

function updateGenerateUI() {
  const isTTS = getSelectedModelType() === "tts";
  generateBtn.textContent = isTTS ? "Generate Speech" : "Generate Insight";
  promptInput.placeholder = isTTS
    ? "Enter text to speak\u2026 supports tags like [laugh], [whispers], [super happy]"
    : "Enter your prompt here\u2026";
}

modelSelect.addEventListener("change", updateGenerateUI);

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

const audioResponse = document.getElementById("audio-response");
const audioPlayer = document.getElementById("audio-player");

generateBtn.addEventListener("click", async () => {
  const prompt = promptInput.value.trim();
  const model = modelSelect.value;
  const isTTS = getSelectedModelType() === "tts";

  if (!prompt) return alert("Please enter a prompt.");
  if (!model) return alert("Please select a model first.");

  generateBtn.disabled = true;
  generateLoader.hidden = false;
  responseDisplay.hidden = true;
  audioResponse.hidden = true;

  try {
    const res = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, model_name: model }),
    });

    if (!res.ok) {
      // Try to parse JSON error from either response type
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || res.statusText);
    }

    if (isTTS) {
      // Response is audio bytes
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      if (audioPlayer.src.startsWith("blob:")) URL.revokeObjectURL(audioPlayer.src);
      audioPlayer.src = url;
      audioResponse.hidden = false;
      audioPlayer.play();
    } else {
      // Response is JSON text
      const data = await res.json();
      responseText.textContent = data.response;
      responseDisplay.hidden = false;
    }
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

/* ── Text-to-Speech (Fish-Audio S2) ──────────────────────── */

const ttsInput = document.getElementById("tts-input");
const ttsBtn = document.getElementById("tts-btn");
const ttsReadBtn = document.getElementById("tts-read-btn");
const ttsLoader = document.getElementById("tts-loader");
const ttsPlayer = document.getElementById("tts-player");
const ttsAudio = document.getElementById("tts-audio");
const ttsError = document.getElementById("tts-error");
const ttsBadge = document.getElementById("tts-badge");

async function checkTTSHealth() {
  try {
    const res = await fetch("/tts/health");
    const data = await res.json();
    if (data.status === "online") {
      ttsBadge.textContent = "online";
      ttsBadge.classList.add("badge-online");
    } else {
      ttsBadge.textContent = "offline";
      ttsBadge.classList.add("badge-offline");
    }
  } catch {
    ttsBadge.textContent = "offline";
    ttsBadge.classList.add("badge-offline");
  }
}

async function synthesize(text) {
  if (!text.trim()) return alert("Enter some text to speak.");

  ttsBtn.disabled = true;
  ttsReadBtn.disabled = true;
  ttsLoader.hidden = false;
  ttsPlayer.hidden = true;
  ttsError.hidden = true;

  try {
    const res = await fetch("/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || res.statusText);
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);

    // Revoke previous object URL to avoid memory leaks
    if (ttsAudio.src.startsWith("blob:")) URL.revokeObjectURL(ttsAudio.src);

    ttsAudio.src = url;
    ttsPlayer.hidden = false;
    ttsAudio.play();
  } catch (err) {
    ttsError.textContent = "TTS failed: " + err.message;
    ttsError.hidden = false;
  } finally {
    ttsBtn.disabled = false;
    ttsReadBtn.disabled = false;
    ttsLoader.hidden = true;
  }
}

ttsBtn.addEventListener("click", () => {
  synthesize(ttsInput.value);
});

ttsReadBtn.addEventListener("click", () => {
  const lastResponse = responseText.textContent;
  if (!lastResponse) return alert("Generate a response first.");
  synthesize(lastResponse);
});

/* ── Init ────────────────────────────────────────────────── */
loadModels();
checkTTSHealth();
