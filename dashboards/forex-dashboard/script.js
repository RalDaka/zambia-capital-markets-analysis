// Stage definitions
const stages = [
  {
    id: "stage1",
    label: "Stage 1",
    script: "Daily6_boz_exchange_rates.py",
    purpose: "Scrape BoZ exchange rates — preview, edit, then inject to Firestore.",
    flow: "forex-exchange-rates",
    status: "not-started",
    draftData: null,
    originalData: null, // snapshot of last fetched data for reset
    source: null, // "web" or "firebase"
  },
  {
    id: "stage2",
    label: "Stage 2",
    script: "Daily7_ForexHistoricPricesAnalysis.py",
    purpose: "Run forex analytics on historic price data.",
    flow: "run-script",
    status: "not-started",
    draftData: null,
  },
];

const els = {};
let pollInterval = null;

document.addEventListener("DOMContentLoaded", () => {
  els.stageGrid = document.getElementById("stageGrid");
  els.logContainer = document.getElementById("logContainer");
  els.logCount = document.getElementById("logCount");
  els.refreshOverviewBtn = document.getElementById("refreshOverviewBtn");
  els.dashboardStatus = document.getElementById("dashboardStatus");
  els.modeStatus = document.getElementById("modeStatus");
  els.activeStageStatus = document.getElementById("activeStageStatus");
  els.lastActionStatus = document.getElementById("lastActionStatus");
  els.statusBadge = document.getElementById("statusBadge");
  els.modeBadge = document.getElementById("modeBadge");

  renderStages();
  loadOverview();
  els.refreshOverviewBtn.addEventListener("click", loadOverview);

  // Poll for status updates every 3 seconds
  pollInterval = setInterval(pollStatus, 3000);
});

function renderStages() {
  els.stageGrid.innerHTML = stages
    .map((stage) => {
      const statusClass = stage.status;
      const statusLabel = formatStatusLabel(stage.status);
      const buttonsHtml = renderButtons(stage);
      const previewHtml = renderPreview(stage);

      return `
        <div class="stage-card" id="card-${stage.id}" data-stage="${stage.id}">
          <div class="stage-card-header">
            <div class="stage-info">
              <h3>${stage.label}</h3>
              <div class="script-name">${stage.script}</div>
              <div class="purpose">${stage.purpose}</div>
            </div>
            <span class="status-badge ${statusClass}" id="status-${stage.id}">
              <span class="dot"></span>
              ${statusLabel}
            </span>
          </div>
          <div class="stage-actions" id="actions-${stage.id}">
            ${buttonsHtml}
          </div>
          <div class="preview-panel" id="preview-${stage.id}">
            ${previewHtml}
          </div>
        </div>
      `;
    })
    .join("");

  // Attach event listeners
  stages.forEach((stage) => {
    const card = document.getElementById(`card-${stage.id}`);

    if (stage.flow === "forex-exchange-rates") {
      const scrapeBtn = card.querySelector(".btn-scrape");
      const firebaseBtn = card.querySelector(".btn-firebase");
      const injectBtn = card.querySelector(".btn-inject");
      const cancelBtn = card.querySelector(".btn-cancel-preview");
      const skipBtn = card.querySelector(".btn-skip");
      const resetBtn = card.querySelector(".btn-reset");
      const clearBtn = card.querySelector(".btn-clear");

      if (scrapeBtn) scrapeBtn.addEventListener("click", () => stage1Scrape(stage));
      if (firebaseBtn) firebaseBtn.addEventListener("click", () => stage1LoadFirebase(stage));
      if (injectBtn) injectBtn.addEventListener("click", () => stage1Inject(stage));
      if (cancelBtn) cancelBtn.addEventListener("click", () => stage1Cancel(stage));
      if (skipBtn) skipBtn.addEventListener("click", () => stageSkip(stage));
      if (resetBtn) resetBtn.addEventListener("click", () => stage1Reset(stage));
      if (clearBtn) clearBtn.addEventListener("click", () => stage1Clear(stage));
    }

    if (stage.flow === "run-script") {
      const runBtn = card.querySelector(".btn-run-script");
      if (runBtn) runBtn.addEventListener("click", () => stage2Run(stage));
    }
  });
}

function renderButtons(stage) {
  switch (stage.flow) {
    case "forex-exchange-rates":
      return `
        <div class="source-selector">
          <button class="source-btn btn-scrape" type="button">🌐 Scrape from Website</button>
          <button class="source-btn btn-firebase" type="button">🔥 Load Current Firebase Data</button>
        </div>
        <button class="danger btn-inject" type="button" disabled>✓ Inject / Confirm</button>
        <button class="btn-cancel-preview" type="button" style="display:none;">✕ Cancel / Reset</button>
        <button class="btn-skip" type="button" style="display:none;">✓ Skip (Already up to date)</button>
      `;

    case "run-script":
      return `
        <button class="primary btn-run-script" type="button">▶ Run Daily7 Script</button>
      `;

    default:
      return "";
  }
}

function renderPreview(stage) {
  if (stage.flow === "forex-exchange-rates") {
    return `
      <div class="preview-title">Exchange Rates — Inspect & Edit</div>
      <div id="preview-content-${stage.id}">
        <span style="color:var(--muted);">Select a source to fetch data.</span>
      </div>
    `;
  }

  if (stage.flow === "run-script") {
    return `
      <div class="preview-title">Script Output</div>
      <pre id="preview-content-${stage.id}" style="color:var(--muted);">Run the script to see output.</pre>
    `;
  }

  return "";
}

function formatStatusLabel(status) {
  switch (status) {
    case "not-started": return "Not started";
    case "running": return "Running";
    case "preview-ready": return "Preview ready";
    case "completed": return "Completed";
    case "error": return "Error";
    default: return status;
  }
}

function updateStageUI(stage) {
  const card = document.getElementById(`card-${stage.id}`);
  const statusEl = document.getElementById(`status-${stage.id}`);
  const actionsEl = document.getElementById(`actions-${stage.id}`);

  if (!card || !statusEl) return;

  // Update status badge
  const statusClass = stage.status;
  const statusLabel = formatStatusLabel(stage.status);
  statusEl.className = `status-badge ${statusClass}`;
  statusEl.innerHTML = `<span class="dot"></span> ${statusLabel}`;

  // Update card active state
  card.classList.toggle("active", stage.status === "running");

  if (stage.flow === "forex-exchange-rates") {
    const isRunning = stage.status === "running";
    const isPreviewReady = stage.status === "preview-ready";

    const scrapeBtn = actionsEl.querySelector(".btn-scrape");
    const firebaseBtn = actionsEl.querySelector(".btn-firebase");
    const injectBtn = actionsEl.querySelector(".btn-inject");
    const cancelBtn = actionsEl.querySelector(".btn-cancel-preview");
    const skipBtn = actionsEl.querySelector(".btn-skip");

    if (scrapeBtn) scrapeBtn.disabled = isRunning;
    if (firebaseBtn) firebaseBtn.disabled = isRunning;
    if (injectBtn) injectBtn.disabled = !isPreviewReady;
    if (cancelBtn) cancelBtn.style.display = isPreviewReady ? "" : "none";

    // Highlight active source button
    if (scrapeBtn) scrapeBtn.classList.toggle("active", stage.source === "web");
    if (firebaseBtn) firebaseBtn.classList.toggle("active", stage.source === "firebase");

    if (skipBtn) {
      if (stage.status !== "preview-ready") {
        skipBtn.style.display = "none";
      }
    }
  }

  if (stage.flow === "run-script") {
    const runBtn = actionsEl.querySelector(".btn-run-script");
    if (runBtn) runBtn.disabled = stage.status === "running";
  }
}

function showPreview(stage, contentHtml) {
  const previewPanel = document.getElementById(`preview-${stage.id}`);
  const previewContent = document.getElementById(`preview-content-${stage.id}`);

  if (previewPanel) previewPanel.classList.add("visible");
  if (previewContent) previewContent.innerHTML = contentHtml;
}

function hidePreview(stage) {
  const previewPanel = document.getElementById(`preview-${stage.id}`);
  if (previewPanel) previewPanel.classList.remove("visible");
}

// ========== Skip / Dismiss ==========

function stageSkip(stage) {
  stage.status = "completed";
  stage.draftData = null;
  stage.originalData = null;
  stage.source = null;
  updateStageUI(stage);
  hidePreview(stage);
  addLog("success", `${stage.label}: Skipped — data already up to date in Firestore.`);
}

// ========== Stage 1: Exchange Rates (Dual Source + Full Editing) ==========

async function stage1Scrape(stage) {
  stage.status = "running";
  stage.source = "web";
  updateStageUI(stage);
  addLog("info", "Stage 1: Scraping BoZ website for exchange rates...");

  try {
    const response = await fetch("/api/forex/exchange-rates/scrape-draft");
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    stage.draftData = data;
    stage.originalData = JSON.parse(JSON.stringify(data)); // deep copy for reset
    stage.status = "preview-ready";
    updateStageUI(stage);

    // Show skip button if data is not new
    const actionsEl = document.getElementById(`actions-${stage.id}`);
    const skipBtn = actionsEl?.querySelector(".btn-skip");
    if (skipBtn) {
      skipBtn.style.display = data.isNewData === false ? "" : "none";
    }

    addLog("success", "Stage 1: Web scrape complete. Draft ready for editing.");
    stage1RenderEditable(stage);
  } catch (err) {
    stage.status = "error";
    stage.source = null;
    updateStageUI(stage);
    addLog("error", `Stage 1 error: ${err.message}`);
  }
}

async function stage1LoadFirebase(stage) {
  stage.status = "running";
  stage.source = "firebase";
  updateStageUI(stage);
  addLog("info", "Stage 1: Loading current exchange rates from Firebase...");

  try {
    const response = await fetch("/api/forex/exchange-rates/firebase");
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    stage.draftData = data;
    stage.originalData = JSON.parse(JSON.stringify(data)); // deep copy for reset
    stage.status = "preview-ready";
    updateStageUI(stage);

    addLog("success", "Stage 1: Firebase data loaded. Ready for editing.");
    stage1RenderEditable(stage);
  } catch (err) {
    stage.status = "error";
    stage.source = null;
    updateStageUI(stage);
    addLog("error", `Stage 1 error: ${err.message}`);
  }
}

function stage1RenderEditable(stage) {
  if (!stage.draftData) {
    addLog("warn", "No draft data to inspect. Select a source first.");
    return;
  }

  const data = stage.draftData;
  const draft = data.draft || {};
  const sourceLabel = stage.source === "firebase" ? "Firebase" : "BoZ Website";

  let html = `<div class="source-indicator">Source: <span class="source-label">${sourceLabel}</span> &nbsp;|&nbsp; Mode: <span class="source-label" style="color:var(--warning);">✏️ Editing</span></div>`;

  // Date field
  html += `
    <div class="edit-field">
      <label>Date</label>
      <input type="text" id="edit-stage1-date" value="${escapeHtml(draft.date || "")}" placeholder="e.g. 26-Apr-26" />
    </div>
  `;

  // Exchange rates editable table
  const rates = draft.exchange_rates || [];
  html += `<div style="margin-top:8px;font-weight:700;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">Exchange Rates</div>`;
  html += `<table class="edit-rates-table" id="edit-stage1-rates-table">`;
  html += `
    <thead>
      <tr>
        <th style="width:100px;">Currency</th>
        <th style="width:120px;">Buying Rate</th>
        <th style="width:120px;">Selling Rate</th>
        <th style="width:50px;"></th>
      </tr>
    </thead>
    <tbody id="edit-stage1-rates-body">
  `;

  rates.forEach((rate, idx) => {
    html += `
      <tr data-index="${idx}">
        <td><input type="text" class="currency-name rate-currency" value="${escapeHtml(rate.currency_name || "")}" placeholder="EUR" /></td>
        <td><input type="number" step="0.0001" class="num rate-buying" value="${rate.buying_rate ?? 0}" /></td>
        <td><input type="number" step="0.0001" class="num rate-selling" value="${rate.selling_rate ?? 0}" /></td>
        <td><button type="button" class="btn-remove-row" onclick="stage1RemoveRateRow(this)">✕</button></td>
      </tr>
    `;
  });

  html += `</tbody></table>`;
  html += `<button type="button" class="btn-add-row" onclick="stage1AddRateRow()">+ Add Currency</button>`;

  // Edit action buttons
  html += `
    <div class="edit-actions">
      <button type="button" class="warning btn-reset" onclick="stage1Reset(stages[0])">↺ Reset to Original</button>
      <button type="button" class="btn-clear" onclick="stage1Clear(stages[0])" style="background:#1a1a2a;color:var(--muted);border-color:var(--line);">✕ Clear Changes</button>
    </div>
  `;

  // Show comparison info
  if (data.current && Object.keys(data.current).length > 0) {
    html += `<div style="margin-top:8px;font-size:11px;color:var(--muted);">Current Firestore: ${escapeHtml(data.current.date || "—")} (${(data.current.exchange_rates || []).length} currencies)</div>`;
  }

  if (data.decision) {
    html += `<div style="margin-top:4px;font-size:11px;color:${data.isNewData === false ? "var(--warning)" : "var(--muted)"};">${escapeHtml(data.decision)}</div>`;
  }

  showPreview(stage, html);
  addLog("info", "Stage 1: Preview ready. Edit fields as needed, then click Inject/Confirm.");
}

function stage1AddRateRow() {
  const tbody = document.getElementById("edit-stage1-rates-body");
  if (!tbody) return;

  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td><input type="text" class="currency-name rate-currency" value="" placeholder="EUR" /></td>
    <td><input type="number" step="0.0001" class="num rate-buying" value="0" /></td>
    <td><input type="number" step="0.0001" class="num rate-selling" value="0" /></td>
    <td><button type="button" class="btn-remove-row" onclick="stage1RemoveRateRow(this)">✕</button></td>
  `;
  tbody.appendChild(tr);
}

function stage1RemoveRateRow(btn) {
  const tr = btn.closest("tr");
  if (tr) tr.remove();
}

function stage1GetEditedPayload(stage) {
  const date = document.getElementById("edit-stage1-date")?.value?.trim() || "";

  const rows = document.querySelectorAll("#edit-stage1-rates-body tr");
  const exchange_rates = [];
  rows.forEach((row) => {
    const currency_name = row.querySelector(".rate-currency")?.value?.trim() || "";
    const buying_rate = parseFloat(row.querySelector(".rate-buying")?.value) || 0;
    const selling_rate = parseFloat(row.querySelector(".rate-selling")?.value) || 0;

    if (currency_name) {
      exchange_rates.push({
        currency_name,
        buying_rate,
        selling_rate,
      });
    }
  });

  return {
    date,
    exchange_rates,
  };
}

function stage1Reset(stage) {
  if (!stage.originalData) {
    addLog("warn", "No original data to reset to.");
    return;
  }

  // Restore draft from original
  stage.draftData = JSON.parse(JSON.stringify(stage.originalData));
  addLog("info", "Stage 1: Reset to original data.");
  stage1RenderEditable(stage);
}

function stage1Clear(stage) {
  if (!stage.draftData) return;

  // Clear all fields in the editable form
  const dateInput = document.getElementById("edit-stage1-date");
  if (dateInput) dateInput.value = "";

  const tbody = document.getElementById("edit-stage1-rates-body");
  if (tbody) {
    const rows = tbody.querySelectorAll("tr");
    rows.forEach((row) => {
      const currencyInput = row.querySelector(".rate-currency");
      const buyingInput = row.querySelector(".rate-buying");
      const sellingInput = row.querySelector(".rate-selling");
      if (currencyInput) currencyInput.value = "";
      if (buyingInput) buyingInput.value = "0";
      if (sellingInput) sellingInput.value = "0";
    });
  }

  addLog("info", "Stage 1: Cleared all fields.");
}

async function stage1Inject(stage) {
  const payload = stage1GetEditedPayload(stage);

  if (!payload.date) {
    addLog("warn", "Date is required.");
    return;
  }

  if (payload.exchange_rates.length === 0) {
    addLog("warn", "At least one exchange rate entry is required.");
    return;
  }

  stage.status = "running";
  updateStageUI(stage);
  addLog("warn", "Stage 1: Injecting exchange rates to Firestore...");

  try {
    const response = await fetch("/api/forex/exchange-rates/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ draft: payload }),
    });

    const result = await response.json();

    if (result.error) {
      throw new Error(result.error);
    }

    stage.status = "completed";
    updateStageUI(stage);
    addLog("success", "Stage 1: Inject complete. Exchange rates saved to Firestore.");
    hidePreview(stage);
  } catch (err) {
    stage.status = "error";
    updateStageUI(stage);
    addLog("error", `Stage 1 error: ${err.message}`);
  }
}

function stage1Cancel(stage) {
  stage.status = "not-started";
  stage.draftData = null;
  stage.originalData = null;
  stage.source = null;
  updateStageUI(stage);
  hidePreview(stage);
  addLog("info", "Stage 1: Cancelled / Reset.");
}

// ========== Stage 2: Forex Analytics (Run Script) ==========

async function stage2Run(stage) {
  stage.status = "running";
  updateStageUI(stage);
  addLog("info", "Stage 2: Running Forex Analytics script...");

  try {
    const response = await fetch("/api/forex/analytics/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const result = await response.json();

    if (result.error) {
      throw new Error(result.error);
    }

    // Store output
    stage.draftData = result;

    // Show output in preview panel
    if (result.stdout) {
      const previewPanel = document.getElementById(`preview-${stage.id}`);
      const previewContent = document.getElementById(`preview-content-${stage.id}`);
      if (previewPanel) previewPanel.classList.add("visible");
      if (previewContent) {
        previewContent.innerHTML = `<pre style="margin:0;white-space:pre-wrap;font-size:12px;">${escapeHtml(result.stdout)}</pre>`;
      }
    }

    if (result.success) {
      stage.status = "completed";
      addLog("success", "Stage 2: Forex Analytics completed successfully.");
    } else {
      stage.status = "error";
      addLog("error", `Stage 2: Script exited with code ${result.returncode}`);
    }

    updateStageUI(stage);
  } catch (err) {
    stage.status = "error";
    updateStageUI(stage);
    addLog("error", `Stage 2 error: ${err.message}`);
  }
}

// ========== Overview & Status Polling ==========

async function loadOverview() {
  try {
    const response = await fetch("/api/overview");
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to load overview.");
    }

    els.dashboardStatus.textContent = `localhost:${data.port}`;
    els.modeStatus.textContent = data.mode === "review-first" ? "Review First" : data.mode;
    els.activeStageStatus.textContent = data.activeStage || "—";
    els.lastActionStatus.textContent = data.lastActionResult
      ? `${data.lastActionResult} (${data.lastActionTime || ""})`
      : "—";

    // Update header badges
    els.modeBadge.textContent = "Review First";
    els.modeBadge.className = "badge green";

    if (data.running) {
      els.statusBadge.textContent = "Running";
      els.statusBadge.className = "badge amber";
    } else {
      els.statusBadge.textContent = "Online";
      els.statusBadge.className = "badge blue";
    }
  } catch (error) {
    els.statusBadge.textContent = "Offline";
    els.statusBadge.className = "badge red";
    addLog("error", `Overview error: ${error.message}`);
  }
}

async function pollStatus() {
  try {
    const response = await fetch("/api/stage/status");
    const data = await response.json();

    if (!response.ok) return;

    // Update overview if there's new info
    if (data.activeStage) {
      els.activeStageStatus.textContent = data.activeStage;
    }
    if (data.lastActionResult) {
      els.lastActionStatus.textContent = `${data.lastActionResult} (${data.lastActionTime || ""})`;
    }

    if (data.running) {
      els.statusBadge.textContent = "Running";
      els.statusBadge.className = "badge amber";
    } else {
      els.statusBadge.textContent = "Online";
      els.statusBadge.className = "badge blue";
    }

    // Sync logs from server
    if (data.logs && data.logs.length > 0) {
      renderLogs(data.logs);
    }
  } catch (err) {
    // Silently fail on poll
  }
}

// ========== Log Panel ==========

function addLog(type, message) {
  const timestamp = new Date().toLocaleTimeString("en-GB", { hour12: false });
  const entry = { time: timestamp, message };

  appendLogEntry(entry);
}

function appendLogEntry(entry) {
  const emptyEl = els.logContainer.querySelector(".log-empty");
  if (emptyEl) emptyEl.remove();

  const div = document.createElement("div");
  div.className = "log-entry";

  // Determine message type for coloring
  let msgClass = "";
  const msg = entry.message.toLowerCase();
  if (msg.includes("error") || msg.includes("fail")) msgClass = "error";
  else if (msg.includes("complete") || msg.includes("success")) msgClass = "success";
  else if (msg.includes("warn") || msg.includes("inject") || msg.includes("confirm")) msgClass = "warn";
  else if (msg.includes("running") || msg.includes("scrape") || msg.includes("inspect") || msg.includes("preview") || msg.includes("load") || msg.includes("edit")) msgClass = "info";

  div.innerHTML = `
    <span class="log-time">${entry.time}</span>
    <span class="log-msg ${msgClass}">${escapeHtml(entry.message)}</span>
  `;

  els.logContainer.appendChild(div);
  els.logContainer.scrollTop = els.logContainer.scrollHeight;

  // Update count
  const entries = els.logContainer.querySelectorAll(".log-entry");
  els.logCount.textContent = `${entries.length} entries`;
}

function renderLogs(logs) {
  // Clear existing log entries (keep empty state)
  const existingEntries = els.logContainer.querySelectorAll(".log-entry");
  existingEntries.forEach((el) => el.remove());

  const emptyEl = els.logContainer.querySelector(".log-empty");
  if (emptyEl) emptyEl.remove();

  logs.forEach((entry) => appendLogEntry(entry));
}

// ========== Utilities ==========

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
