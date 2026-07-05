// Stage definitions
const stages = [
  {
    id: "stage1",
    label: "Stage 1",
    script: "Monthly_Stage1_Boz_Bond_Invitations.py",
    purpose: "Scrape BoZ bond invitations and review before saving to Firestore.",
    flow: "scrape-inspect-inject",
    status: "not-started",
    draftData: null,
    source: null, // "web" or "firebase"
  },
  {
    id: "stage1a",
    label: "Stage 1a",
    script: "Monthly_Stage1a_Boz_Bond_Notifications.py",
    purpose: "Preview and send bond invitation notification to users.",
    flow: "run-with-confirm",
    status: "not-started",
    draftData: null,
  },
  {
    id: "stage2",
    label: "Stage 2",
    script: "Monthly_Stage2_Boz_Bond_yield_rates.py",
    purpose: "Scrape bond yield rates — preview first, then run the existing script to save.",
    flow: "scrape-inspect-inject-yield",
    status: "not-started",
    draftData: null,
    source: null, // "web" or "firebase"
  },
  {
    id: "stage2a",
    label: "Stage 2a",
    script: "Monthly_Stage2a_Boz_Bond_Yield_Notifications.py",
    purpose: "Preview and send yield rate notification to users.",
    flow: "run-with-confirm",
    status: "not-started",
    draftData: null,
  },
  {
    id: "stage3",
    label: "Stage 3",
    script: "Monthly_Stage3_Boz_Bond_add_new_yieldRates_to_Historic_Yields.py",
    purpose: "Sync yield rates into historic yield collections.",
    flow: "run-inspect-confirm",
    status: "not-started",
    draftData: null,
  },
  {
    id: "stage4",
    label: "Stage 4",
    script: "Monthly_Stage4_Boz_Bond_AmountBidAllocated.py",
    purpose: "Fetch and update amount bid/allocated data from BoZ PDF.",
    flow: "run-inspect-confirm",
    status: "not-started",
    draftData: null,
  },
  {
    id: "stage5",
    label: "Stage 5",
    script: "Monthly_Stage5_Boz_Bond_Analysis.py",
    purpose: "Calculate bond analytics on historic data.",
    flow: "run-inspect-confirm",
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
  els.scriptsStatus = document.getElementById("scriptsStatus");
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

    if (stage.flow === "scrape-inspect-inject") {
      const scrapeBtn = card.querySelector(".btn-scrape");
      const firebaseBtn = card.querySelector(".btn-firebase");
      const inspectBtn = card.querySelector(".btn-inspect");
      const injectBtn = card.querySelector(".btn-inject");
      const cancelBtn = card.querySelector(".btn-cancel-preview");
      const skipBtn = card.querySelector(".btn-skip");

      if (scrapeBtn) scrapeBtn.addEventListener("click", () => stage1Scrape(stage));
      if (firebaseBtn) firebaseBtn.addEventListener("click", () => stage1LoadFirebase(stage));
      if (inspectBtn) inspectBtn.addEventListener("click", () => stage1Inspect(stage));
      if (injectBtn) injectBtn.addEventListener("click", () => stage1Inject(stage));
      if (cancelBtn) cancelBtn.addEventListener("click", () => stage1Cancel(stage));
      if (skipBtn) skipBtn.addEventListener("click", () => stageSkip(stage));
    }

    if (stage.flow === "scrape-inspect-inject-yield") {
      const scrapeBtn = card.querySelector(".btn-scrape");
      const firebaseBtn = card.querySelector(".btn-firebase");
      const inspectBtn = card.querySelector(".btn-inspect");
      const injectBtn = card.querySelector(".btn-inject");
      const cancelBtn = card.querySelector(".btn-cancel-preview");
      const skipBtn = card.querySelector(".btn-skip");

      if (scrapeBtn) scrapeBtn.addEventListener("click", () => stage2Scrape(stage));
      if (firebaseBtn) firebaseBtn.addEventListener("click", () => stage2LoadFirebase(stage));
      if (inspectBtn) inspectBtn.addEventListener("click", () => stage2Inspect(stage));
      if (injectBtn) injectBtn.addEventListener("click", () => stage2Inject(stage));
      if (cancelBtn) cancelBtn.addEventListener("click", () => stage2Cancel(stage));
      if (skipBtn) skipBtn.addEventListener("click", () => stageSkip(stage));
    }

    if (stage.flow === "run-with-confirm") {
      const runBtn = card.querySelector(".btn-run");
      const inspectBtn = card.querySelector(".btn-inspect");
      const confirmBtn = card.querySelector(".btn-confirm");
      const cancelBtn = card.querySelector(".btn-cancel");

      if (runBtn) runBtn.addEventListener("click", () => stageRunWithPreview(stage));
      if (inspectBtn) inspectBtn.addEventListener("click", () => stageInspectOutput(stage));
      if (confirmBtn) confirmBtn.addEventListener("click", () => stageConfirm(stage, true));
      if (cancelBtn) cancelBtn.addEventListener("click", () => stageConfirm(stage, false));
    }

    if (stage.flow === "run-script") {
      const runBtn = card.querySelector(".btn-run-script");
      if (runBtn) runBtn.addEventListener("click", () => stageRunScript(stage));
    }

    if (stage.flow === "run-inspect-confirm") {
      const runBtn = card.querySelector(".btn-run-script");
      const inspectBtn = card.querySelector(".btn-inspect");
      const confirmBtn = card.querySelector(".btn-confirm");
      const cancelBtn = card.querySelector(".btn-cancel");

      if (runBtn) runBtn.addEventListener("click", () => stageRunWithInspect(stage));
      if (inspectBtn) inspectBtn.addEventListener("click", () => stageInspectOutput(stage));
      if (confirmBtn) confirmBtn.addEventListener("click", () => stageConfirmRun(stage, true));
      if (cancelBtn) cancelBtn.addEventListener("click", () => stageConfirmRun(stage, false));
    }
  });
}

function renderButtons(stage) {
  switch (stage.flow) {
    case "scrape-inspect-inject":
      return `
        <div class="source-selector">
          <button class="source-btn btn-scrape" type="button">🌐 Scrape from Website</button>
          <button class="source-btn btn-firebase" type="button">🔥 Load Current Firebase Data</button>
        </div>
        <button class="warning btn-inspect" type="button" disabled>Inspect / Edit</button>
        <button class="danger btn-inject" type="button" disabled>Inject to Firestore</button>
        <button class="btn-cancel-preview" type="button" style="display:none;">✕ Cancel / Reset</button>
        <button class="btn-skip" type="button" style="display:none;">✓ Skip (Already up to date)</button>
      `;

    case "scrape-inspect-inject-yield":
      return `
        <div class="source-selector">
          <button class="source-btn btn-scrape" type="button">🌐 Scrape from Website</button>
          <button class="source-btn btn-firebase" type="button">🔥 Load Current Firebase Data</button>
        </div>
        <button class="warning btn-inspect" type="button" disabled>Inspect / Edit</button>
        <button class="danger btn-inject" type="button" disabled>Inject to Firestore</button>
        <button class="btn-cancel-preview" type="button" style="display:none;">✕ Cancel / Reset</button>
        <button class="btn-skip" type="button" style="display:none;">✓ Skip (Already up to date)</button>
      `;

    case "run-with-confirm":
      return `
        <button class="primary btn-run" type="button">Run Existing Script</button>
        <button class="warning btn-inspect" type="button" disabled>Inspect Output</button>
        <button class="success btn-confirm" type="button" style="display:none;">✓ Send Notification</button>
        <button class="danger btn-cancel" type="button" style="display:none;">✕ Don't Send</button>
      `;

    case "run-script":
      return `
        <button class="primary btn-run-script" type="button">Run Existing Script</button>
      `;

    case "run-inspect-confirm":
      return `
        <button class="primary btn-run-script" type="button">Run Script</button>
        <button class="warning btn-inspect" type="button" disabled>Inspect Output</button>
        <button class="success btn-confirm" type="button" style="display:none;">✓ Confirm & Complete</button>
        <button class="danger btn-cancel" type="button" style="display:none;">✕ Cancel</button>
      `;

    default:
      return "";
  }
}

function renderPreview(stage) {
  if (stage.flow === "scrape-inspect-inject" || stage.flow === "scrape-inspect-inject-yield") {
    return `
      <div class="preview-title">Preview Data</div>
      <div id="preview-content-${stage.id}">
        <span style="color:var(--muted);">Select a source to fetch data.</span>
      </div>
    `;
  }

  if (stage.flow === "run-with-confirm") {
    return `
      <div class="preview-title">Script Output Preview</div>
      <pre id="preview-content-${stage.id}" style="color:var(--muted);">Run the script to see output.</pre>
    `;
  }

  if (stage.flow === "run-inspect-confirm") {
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

  // Re-render buttons based on state
  const scrapeBtn = actionsEl.querySelector(".btn-scrape");
  const firebaseBtn = actionsEl.querySelector(".btn-firebase");
  const inspectBtn = actionsEl.querySelector(".btn-inspect");
  const injectBtn = actionsEl.querySelector(".btn-inject");
  const cancelBtn = actionsEl.querySelector(".btn-cancel-preview");
  const runBtn = actionsEl.querySelector(".btn-run");
  const confirmBtn = actionsEl.querySelector(".btn-confirm");
  const cancelConfirmBtn = actionsEl.querySelector(".btn-cancel");
  const runScriptBtn = actionsEl.querySelector(".btn-run-script");

  if (stage.flow === "scrape-inspect-inject" || stage.flow === "scrape-inspect-inject-yield") {
    const isRunning = stage.status === "running";
    const isPreviewReady = stage.status === "preview-ready";

    if (scrapeBtn) scrapeBtn.disabled = isRunning;
    if (firebaseBtn) firebaseBtn.disabled = isRunning;
    if (inspectBtn) inspectBtn.disabled = !isPreviewReady;
    if (injectBtn) injectBtn.disabled = !isPreviewReady;
    if (cancelBtn) cancelBtn.style.display = isPreviewReady ? "" : "none";

    // Highlight active source button
    if (scrapeBtn) scrapeBtn.classList.toggle("active", stage.source === "web");
    if (firebaseBtn) firebaseBtn.classList.toggle("active", stage.source === "firebase");

    // Hide skip button when leaving preview-ready state
    const skipBtn = actionsEl.querySelector(".btn-skip");
    if (skipBtn) {
      if (stage.status !== "preview-ready") {
        skipBtn.style.display = "none";
      }
    }
  }

  if (stage.flow === "run-with-confirm") {
    if (runBtn) {
      runBtn.style.display = stage.status === "preview-ready" ? "none" : "";
      runBtn.disabled = stage.status === "running";
    }
    if (inspectBtn) {
      inspectBtn.style.display = stage.status === "preview-ready" ? "" : "none";
      inspectBtn.disabled = stage.status !== "preview-ready";
    }
    if (confirmBtn) confirmBtn.style.display = stage.status === "preview-ready" ? "" : "none";
    if (cancelConfirmBtn) cancelConfirmBtn.style.display = stage.status === "preview-ready" ? "" : "none";
  }

  if (stage.flow === "run-script") {
    if (runScriptBtn) runScriptBtn.disabled = stage.status === "running";
  }

  if (stage.flow === "run-inspect-confirm") {
    if (runScriptBtn) {
      runScriptBtn.style.display = stage.status === "preview-ready" ? "none" : "";
      runScriptBtn.disabled = stage.status === "running";
    }
    if (inspectBtn) {
      inspectBtn.style.display = stage.status === "preview-ready" ? "" : "none";
      inspectBtn.disabled = stage.status !== "preview-ready";
    }
    if (confirmBtn) confirmBtn.style.display = stage.status === "preview-ready" ? "" : "none";
    if (cancelConfirmBtn) cancelConfirmBtn.style.display = stage.status === "preview-ready" ? "" : "none";
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

// ========== Skip / Dismiss (for scrape-inspect-inject stages) ==========

function stageSkip(stage) {
  stage.status = "completed";
  stage.draftData = null;
  stage.source = null;
  updateStageUI(stage);
  hidePreview(stage);
  addLog("success", `${stage.label}: Skipped — data already up to date in Firestore.`);
}

// ========== Stage 1: Invitations (Dual Source) ==========

async function stage1Scrape(stage) {
  stage.status = "running";
  stage.source = "web";
  updateStageUI(stage);
  addLog("info", "Stage 1: Scraping BoZ website for invitations...");

  try {
    const response = await fetch("/api/bond/invitations/scrape-draft");
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    stage.draftData = data;
    stage.status = "preview-ready";
    updateStageUI(stage);

    // Show skip button if data is not new (already in Firestore)
    const actionsEl = document.getElementById(`actions-${stage.id}`);
    const skipBtn = actionsEl?.querySelector(".btn-skip");
    if (skipBtn) {
      skipBtn.style.display = data.isNewData === false ? "" : "none";
    }

    addLog("success", "Stage 1: Web scrape complete. Draft ready.");
    stage1Inspect(stage);
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
  addLog("info", "Stage 1: Loading current invitation data from Firebase...");

  try {
    const response = await fetch("/api/bond/invitations/firebase");
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    stage.draftData = data;
    stage.status = "preview-ready";
    updateStageUI(stage);

    addLog("success", "Stage 1: Firebase data loaded. Ready for editing.");
    stage1Inspect(stage);
  } catch (err) {
    stage.status = "error";
    stage.source = null;
    updateStageUI(stage);
    addLog("error", `Stage 1 error: ${err.message}`);
  }
}

function stage1Inspect(stage) {
  if (!stage.draftData) {
    addLog("warn", "No draft data to inspect. Select a source first.");
    return;
  }

  const data = stage.draftData;
  const draft = data.draft || {};
  const sourceLabel = stage.source === "firebase" ? "Firebase" : "BoZ Website";

  let html = `<div class="source-indicator">Source: <span class="source-label">${sourceLabel}</span></div>`;

  // Editable form fields
  html += `
    <div class="edit-field">
      <label>Tender Number</label>
      <input type="text" id="edit-stage1-tenderNumber" value="${escapeHtml(draft.tenderNumber || "")}" />
    </div>
    <div class="edit-field">
      <label>Bid Submission Deadline</label>
      <input type="text" id="edit-stage1-deadline" value="${escapeHtml(draft.bidSubmissionDeadlineString || "")}" />
    </div>
    <div class="edit-field">
      <label>Settlement Date</label>
      <input type="text" id="edit-stage1-settlement" value="${escapeHtml(draft.settlementDate || "")}" />
    </div>
    <div class="edit-field">
      <label>PDF URL</label>
      <input type="text" id="edit-stage1-pdfUrl" value="${escapeHtml(draft.pdfUrl || "")}" />
    </div>
  `;

  // Show comparison if web scrape
  if (data.current && Object.keys(data.current).length > 0) {
    html += `<div style="margin-top:8px;font-size:11px;color:var(--muted);">Current Firestore: Tender ${escapeHtml(data.current.tenderNumber || "—")}</div>`;
  }

  if (data.decision) {
    html += `<div style="margin-top:4px;font-size:11px;color:${data.isNewData === false ? "var(--warning)" : "var(--muted)"};">${escapeHtml(data.decision)}</div>`;
  }

  showPreview(stage, html);
  addLog("info", "Stage 1: Preview ready. Edit fields as needed, then click Inject.");
}

function stage1GetEditedPayload(stage) {
  const tenderNumber = document.getElementById("edit-stage1-tenderNumber")?.value?.trim() || "";
  const deadline = document.getElementById("edit-stage1-deadline")?.value?.trim() || "";
  const settlement = document.getElementById("edit-stage1-settlement")?.value?.trim() || "";
  const pdfUrl = document.getElementById("edit-stage1-pdfUrl")?.value?.trim() || "";

  const payload = {
    tenderNumber,
    bidSubmissionDeadlineString: deadline,
    settlementDate: settlement,
  };

  if (pdfUrl) {
    payload.pdfUrl = pdfUrl;
  }

  return payload;
}

async function stage1Inject(stage) {
  const payload = stage1GetEditedPayload(stage);

  if (!payload.tenderNumber) {
    addLog("warn", "Tender number is required.");
    return;
  }

  stage.status = "running";
  updateStageUI(stage);
  addLog("warn", "Stage 1: Injecting invitation data to Firestore...");

  try {
    const response = await fetch("/api/bond/invitations/ingest", {
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
    addLog("success", "Stage 1: Inject complete.");
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
  stage.source = null;
  updateStageUI(stage);
  hidePreview(stage);
  addLog("info", "Stage 1: Cancelled / Reset.");
}

// ========== Stage 2: Yield Rates (Dual Source) ==========

async function stage2Scrape(stage) {
  stage.status = "running";
  stage.source = "web";
  updateStageUI(stage);
  addLog("info", "Stage 2: Scraping BoZ website for yield rates...");

  try {
    const response = await fetch("/api/bond/yields/scrape-draft");
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    stage.draftData = data;
    stage.status = "preview-ready";
    updateStageUI(stage);

    // Show skip button if data is not new (already in Firestore)
    const actionsEl = document.getElementById(`actions-${stage.id}`);
    const skipBtn = actionsEl?.querySelector(".btn-skip");
    if (skipBtn) {
      skipBtn.style.display = data.isNewData === false ? "" : "none";
    }

    addLog("success", "Stage 2: Web scrape complete. Draft ready.");
    stage2Inspect(stage);
  } catch (err) {
    stage.status = "error";
    stage.source = null;
    updateStageUI(stage);
    addLog("error", `Stage 2 error: ${err.message}`);
  }
}

async function stage2LoadFirebase(stage) {
  stage.status = "running";
  stage.source = "firebase";
  updateStageUI(stage);
  addLog("info", "Stage 2: Loading current yield data from Firebase...");

  try {
    const response = await fetch("/api/bond/yields/firebase");
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    stage.draftData = data;
    stage.status = "preview-ready";
    updateStageUI(stage);

    addLog("success", "Stage 2: Firebase data loaded. Ready for editing.");
    stage2Inspect(stage);
  } catch (err) {
    stage.status = "error";
    stage.source = null;
    updateStageUI(stage);
    addLog("error", `Stage 2 error: ${err.message}`);
  }
}

function stage2Inspect(stage) {
  if (!stage.draftData) {
    addLog("warn", "No draft data to inspect. Select a source first.");
    return;
  }

  const data = stage.draftData;
  const draft = data.draft || {};
  const sourceLabel = stage.source === "firebase" ? "Firebase" : "BoZ Website";

  let html = `<div class="source-indicator">Source: <span class="source-label">${sourceLabel}</span></div>`;

  // Tender number field
  html += `
    <div class="edit-field">
      <label>Tender Number</label>
      <input type="text" id="edit-stage2-tenderNo" value="${escapeHtml(draft.tender_no || "")}" />
    </div>
  `;

  // Bonds table - editable rows
  const bonds = draft.bonds || [];
  if (bonds.length > 0) {
    html += `<div style="margin-top:8px;font-weight:700;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">Bonds</div>`;
    html += `<div id="edit-stage2-bonds-container">`;
    bonds.forEach((bond, idx) => {
      html += `
        <div class="edit-row" data-index="${idx}">
          <label>Period</label>
          <input type="text" class="edit-bond-period" value="${escapeHtml(bond.period || "")}" />
          <label>ISIN</label>
          <input type="text" class="edit-bond-isin" value="${escapeHtml(bond.isin || "")}" style="flex:1.5;" />
          <label>Yield</label>
          <input type="number" step="0.0001" class="num edit-bond-yield" value="${bond.yield ?? 0}" />
          <label>Coupon</label>
          <input type="number" step="0.0001" class="num edit-bond-coupon" value="${bond.coupon ?? 0}" />
          <label>Change</label>
          <input type="number" step="0.0001" class="num edit-bond-change" value="${bond.change ?? 0}" />
        </div>
      `;
    });
    html += `</div>`;
  } else {
    html += `<div style="margin-top:8px;color:var(--muted);">No bond entries found.</div>`;
  }

  if (data.decision) {
    html += `<div style="margin-top:8px;font-size:11px;color:${data.isNewData === false ? "var(--warning)" : "var(--muted)"};">${escapeHtml(data.decision)}</div>`;
  }

  showPreview(stage, html);
  addLog("info", "Stage 2: Preview ready. Edit fields as needed, then click Inject.");
}

function stage2GetEditedPayload(stage) {
  const tenderNo = document.getElementById("edit-stage2-tenderNo")?.value?.trim() || "";

  const bondRows = document.querySelectorAll("#edit-stage2-bonds-container .edit-row");
  const bonds = [];
  bondRows.forEach((row) => {
    const period = row.querySelector(".edit-bond-period")?.value?.trim() || "";
    const isin = row.querySelector(".edit-bond-isin")?.value?.trim() || "";
    const yieldVal = parseFloat(row.querySelector(".edit-bond-yield")?.value) || 0;
    const couponVal = parseFloat(row.querySelector(".edit-bond-coupon")?.value) || 0;
    const changeVal = parseFloat(row.querySelector(".edit-bond-change")?.value) || 0;

    if (period) {
      bonds.push({
        period,
        isin,
        yield: yieldVal,
        coupon: couponVal,
        change: changeVal,
      });
    }
  });

  return {
    tender_no: tenderNo,
    bonds,
  };
}

async function stage2Inject(stage) {
  const payload = stage2GetEditedPayload(stage);

  if (!payload.tender_no) {
    addLog("warn", "Tender number is required.");
    return;
  }

  if (payload.bonds.length === 0) {
    addLog("warn", "At least one bond entry is required.");
    return;
  }

  stage.status = "running";
  updateStageUI(stage);
  addLog("warn", "Stage 2: Injecting yield data to Firestore...");

  try {
    const response = await fetch("/api/bond/yields/ingest", {
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
    addLog("success", "Stage 2: Yield inject complete.");
    hidePreview(stage);
  } catch (err) {
    stage.status = "error";
    updateStageUI(stage);
    addLog("error", `Stage 2 error: ${err.message}`);
  }
}

function stage2Cancel(stage) {
  stage.status = "not-started";
  stage.draftData = null;
  stage.source = null;
  updateStageUI(stage);
  hidePreview(stage);
  addLog("info", "Stage 2: Cancelled / Reset.");
}

// ========== Stages with Confirm/Cancel (1a, 2a) ==========

async function stageRunWithPreview(stage) {
  stage.status = "running";
  updateStageUI(stage);
  addLog("info", `Running ${stage.label} for preview...`);

  try {
    // Run without confirm first to capture the preview output
    const response = await fetch("/api/stage/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stage: stage.id, confirm: false }),
    });

    const result = await response.json();

    if (result.error) {
      throw new Error(result.error);
    }

    // Store the output for later confirmation
    stage.draftData = result;

    if (result.stdout) {
      showPreview(stage, escapeHtml(result.stdout));
    }

    // Check if the script completed without needing confirmation (e.g., already up to date)
    const output = (result.stdout || "").toLowerCase();
    const alreadySent = output.includes("already sent") || output.includes("skipping");

    if (alreadySent && result.success) {
      // Script completed without needing user confirmation (idempotency check passed)
      stage.status = "completed";
      updateStageUI(stage);
      addLog("success", `${stage.label} completed successfully.`);
    } else {
      // Script needs user confirmation (preview mode piped "n")
      stage.status = "preview-ready";
      updateStageUI(stage);
      addLog("info", "Preview ready. Review output above, then Confirm to send or Cancel.");
    }
  } catch (err) {
    stage.status = "error";
    updateStageUI(stage);
    addLog("error", `Error: ${err.message}`);
  }
}

async function stageConfirm(stage, confirmed) {
  if (!stage.draftData) {
    addLog("warn", "No preview data. Run the script first.");
    return;
  }

  if (!confirmed) {
    stage.status = "not-started";
    stage.draftData = null;
    updateStageUI(stage);
    hidePreview(stage);
    addLog("info", `${stage.label} cancelled by user.`);
    return;
  }

  stage.status = "running";
  updateStageUI(stage);
  addLog("warn", `${stage.label} confirmed. Sending...`);

  try {
    const response = await fetch("/api/stage/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stage: stage.id, confirm: true }),
    });

    const result = await response.json();

    if (result.error) {
      throw new Error(result.error);
    }

    if (result.stdout) {
      showPreview(stage, escapeHtml(result.stdout));
    }

    if (result.success) {
      stage.status = "completed";
      addLog("success", `${stage.label} completed successfully.`);
    } else {
      stage.status = "error";
      addLog("error", `${stage.label} exited with code ${result.returncode}`);
    }

    updateStageUI(stage);
  } catch (err) {
    stage.status = "error";
    updateStageUI(stage);
    addLog("error", `Error: ${err.message}`);
  }
}

// ========== Stages 3, 4, 5: Run → Inspect → Confirm ==========

async function stageRunWithInspect(stage) {
  stage.status = "running";
  updateStageUI(stage);
  addLog("info", `Running ${stage.label}...`);

  try {
    const response = await fetch("/api/stage/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stage: stage.id, confirm: false }),
    });

    const result = await response.json();

    if (result.error) {
      throw new Error(result.error);
    }

    // Store the output for later inspection
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
      stage.status = "preview-ready";
      addLog("success", `${stage.label} ran successfully. Inspect output, then Confirm or Cancel.`);
    } else {
      stage.status = "error";
      addLog("error", `${stage.label} exited with code ${result.returncode}`);
    }

    updateStageUI(stage);
  } catch (err) {
    stage.status = "error";
    updateStageUI(stage);
    addLog("error", `Error: ${err.message}`);
  }
}

function stageInspectOutput(stage) {
  if (!stage.draftData || !stage.draftData.stdout) {
    addLog("warn", "No output to inspect. Run the script first.");
    return;
  }

  const previewPanel = document.getElementById(`preview-${stage.id}`);
  const previewContent = document.getElementById(`preview-content-${stage.id}`);
  if (previewPanel) previewPanel.classList.add("visible");
  if (previewContent) {
    previewContent.innerHTML = `<pre style="margin:0;white-space:pre-wrap;font-size:12px;">${escapeHtml(stage.draftData.stdout)}</pre>`;
  }

  addLog("info", `Inspecting ${stage.label} output.`);
}

async function stageConfirmRun(stage, confirmed) {
  if (!confirmed) {
    stage.status = "not-started";
    stage.draftData = null;
    updateStageUI(stage);
    hidePreview(stage);
    addLog("info", `${stage.label} cancelled by user.`);
    return;
  }

  stage.status = "completed";
  stage.draftData = null;
  updateStageUI(stage);
  addLog("success", `${stage.label} confirmed and marked as completed.`);
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
    els.scriptsStatus.textContent = `${data.scriptsFound} / ${data.scriptsExpected} found`;
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

    // Check for missing scripts
    if (data.missing && data.missing.length > 0) {
      addLog("warn", `Missing scripts: ${data.missing.join(", ")}`);
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

    // Update header badge
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

  // Also send to server via status endpoint (best-effort)
  // The server already logs via its own add_log, so we just render locally
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
  else if (msg.includes("running") || msg.includes("scrape") || msg.includes("inspect") || msg.includes("preview") || msg.includes("load")) msgClass = "info";

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
