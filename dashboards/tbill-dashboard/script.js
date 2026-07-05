// Stage definitions
const stages = [
  {
    id: "stage1",
    label: "Stage 1",
    script: "Monthly_Stage1_Boz_TBill_Invitations.py",
    purpose: "Scrape BoZ T-Bill invitations and review before saving to Firestore.",
    flow: "scrape-inspect-inject",
    status: "not-started",
    draftData: null,
  },
  {
    id: "stage1a",
    label: "Stage 1a",
    script: "Monthly_Stage1a_Boz_TBill_Notifications.py",
    purpose: "Preview and send T-Bill invitation notification to users.",
    flow: "run-with-confirm",
    status: "not-started",
    draftData: null,
  },
  {
    id: "stage2",
    label: "Stage 2",
    script: "Monthly_Stage2_Boz_TBill_yield_rates.py",
    purpose: "Scrape T-Bill yield rates — preview first, then run the existing script to save.",
    flow: "scrape-inspect-inject-yield",
    status: "not-started",
    draftData: null,
  },
  {
    id: "stage2a",
    label: "Stage 2a",
    script: "Monthly_Stage2a_Boz_TBill_Yield_Notifications.py",
    purpose: "Preview and send yield rate notification to users.",
    flow: "run-with-confirm",
    status: "not-started",
    draftData: null,
  },
  {
    id: "stage3",
    label: "Stage 3",
    script: "Monthly_Stage3_Boz_TBill_add_new_yieldRates_to_Historic_Yields.py",
    purpose: "Sync yield rates into historic yield collections.",
    flow: "run-inspect-confirm",
    status: "not-started",
    draftData: null,
  },
  {
    id: "stage4",
    label: "Stage 4",
    script: "Monthly_Stage4_Boz_TBill_AmountBidAllocated.py",
    purpose: "Fetch and update amount bid/allocated data from BoZ PDF.",
    flow: "run-inspect-confirm",
    status: "not-started",
    draftData: null,
  },
  {
    id: "stage5",
    label: "Stage 5",
    script: "Monthly_Stage5_Boz_TBill_Analysis.py",
    purpose: "Calculate T-Bill analytics on historic data.",
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
      const scrapeWebBtn = card.querySelector(".btn-scrape-web");
      const scrapeFirebaseBtn = card.querySelector(".btn-scrape-firebase");
      const injectBtn = card.querySelector(".btn-inject");
      const cancelBtn = card.querySelector(".btn-cancel-edit");
      const skipBtn = card.querySelector(".btn-skip");

      if (scrapeWebBtn) scrapeWebBtn.addEventListener("click", () => stage1ScrapeWeb(stage));
      if (scrapeFirebaseBtn) scrapeFirebaseBtn.addEventListener("click", () => stage1ScrapeFirebase(stage));
      if (injectBtn) injectBtn.addEventListener("click", () => stage1Inject(stage));
      if (cancelBtn) cancelBtn.addEventListener("click", () => stage1Cancel(stage));
      if (skipBtn) skipBtn.addEventListener("click", () => stageSkip(stage));
    }

    if (stage.flow === "scrape-inspect-inject-yield") {
      const scrapeWebBtn = card.querySelector(".btn-scrape-web");
      const scrapeFirebaseBtn = card.querySelector(".btn-scrape-firebase");
      const injectBtn = card.querySelector(".btn-inject");
      const cancelBtn = card.querySelector(".btn-cancel-edit");
      const skipBtn = card.querySelector(".btn-skip");

      if (scrapeWebBtn) scrapeWebBtn.addEventListener("click", () => stage2ScrapeWeb(stage));
      if (scrapeFirebaseBtn) scrapeFirebaseBtn.addEventListener("click", () => stage2ScrapeFirebase(stage));
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
          <button class="primary btn-scrape-web" type="button">🌐 Scrape from Website</button>
          <button class="success btn-scrape-firebase" type="button">🔥 Load Current Firebase Data</button>
        </div>
        <button class="danger btn-inject" type="button" disabled>Inject to Firestore</button>
        <button class="warning btn-cancel-edit" type="button" style="display:none;">✕ Cancel / Reset</button>
        <button class="btn-skip" type="button" style="display:none;">✓ Skip (Already up to date)</button>
      `;

    case "scrape-inspect-inject-yield":
      return `
        <div class="source-selector">
          <button class="primary btn-scrape-web" type="button">🌐 Scrape from Website</button>
          <button class="success btn-scrape-firebase" type="button">🔥 Load Current Firebase Data</button>
        </div>
        <button class="danger btn-inject" type="button" disabled>Inject to Firestore</button>
        <button class="warning btn-cancel-edit" type="button" style="display:none;">✕ Cancel / Reset</button>
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
        <span style="color:var(--muted);">Run Scrape to fetch data.</span>
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
  const scrapeWebBtn = actionsEl.querySelector(".btn-scrape-web");
  const scrapeFirebaseBtn = actionsEl.querySelector(".btn-scrape-firebase");
  const injectBtn = actionsEl.querySelector(".btn-inject");
  const cancelEditBtn = actionsEl.querySelector(".btn-cancel-edit");
  const runBtn = actionsEl.querySelector(".btn-run");
  const confirmBtn = actionsEl.querySelector(".btn-confirm");
  const cancelBtn = actionsEl.querySelector(".btn-cancel");
  const runScriptBtn = actionsEl.querySelector(".btn-run-script");

  if (stage.flow === "scrape-inspect-inject" || stage.flow === "scrape-inspect-inject-yield") {
    if (scrapeWebBtn) scrapeWebBtn.disabled = stage.status === "running";
    if (scrapeFirebaseBtn) scrapeFirebaseBtn.disabled = stage.status === "running";
    if (injectBtn) injectBtn.disabled = stage.status !== "preview-ready";

    // Hide skip button when leaving preview-ready state
    const skipBtn = actionsEl.querySelector(".btn-skip");
    if (skipBtn) {
      if (stage.status !== "preview-ready") {
        skipBtn.style.display = "none";
      }
    }
  }

  if (stage.flow === "run-with-confirm") {
    const runBtnEl = actionsEl.querySelector(".btn-run");
    const inspectBtnEl = actionsEl.querySelector(".btn-inspect");
    const confirmBtnEl = actionsEl.querySelector(".btn-confirm");
    const cancelBtnEl = actionsEl.querySelector(".btn-cancel");

    if (runBtnEl) {
      runBtnEl.style.display = stage.status === "preview-ready" ? "none" : "";
      runBtnEl.disabled = stage.status === "running";
    }
    if (inspectBtnEl) {
      inspectBtnEl.style.display = stage.status === "preview-ready" ? "" : "none";
      inspectBtnEl.disabled = stage.status !== "preview-ready";
    }
    if (confirmBtnEl) confirmBtnEl.style.display = stage.status === "preview-ready" ? "" : "none";
    if (cancelBtnEl) cancelBtnEl.style.display = stage.status === "preview-ready" ? "" : "none";
  }

  if (stage.flow === "run-script") {
    const runScriptBtnEl = actionsEl.querySelector(".btn-run-script");
    if (runScriptBtnEl) runScriptBtnEl.disabled = stage.status === "running";
  }

  if (stage.flow === "run-inspect-confirm") {
    const runScriptBtnEl = actionsEl.querySelector(".btn-run-script");
    const inspectBtnEl = actionsEl.querySelector(".btn-inspect");
    const confirmBtnEl = actionsEl.querySelector(".btn-confirm");
    const cancelBtnEl = actionsEl.querySelector(".btn-cancel");

    if (runScriptBtnEl) {
      runScriptBtnEl.style.display = stage.status === "preview-ready" ? "none" : "";
      runScriptBtnEl.disabled = stage.status === "running";
    }
    if (inspectBtnEl) {
      inspectBtnEl.style.display = stage.status === "preview-ready" ? "" : "none";
      inspectBtnEl.disabled = stage.status !== "preview-ready";
    }
    if (confirmBtnEl) confirmBtnEl.style.display = stage.status === "preview-ready" ? "" : "none";
    if (cancelBtnEl) cancelBtnEl.style.display = stage.status === "preview-ready" ? "" : "none";
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
  updateStageUI(stage);
  hidePreview(stage);
  addLog("success", `${stage.label}: Skipped — data already up to date in Firestore.`);
}

// ========== Stage 1: Invitations — Dual Source (Web / Firebase) ==========

async function stage1ScrapeWeb(stage) {
  stage.status = "running";
  updateStageUI(stage);
  addLog("info", "Stage 1: Scraping from BoZ website...");

  try {
    const response = await fetch("/api/tbill/invitations/scrape-draft");
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    stage.draftData = data;
    stage.status = "preview-ready";
    updateStageUI(stage);

    // Show skip button if data is not new
    const actionsEl = document.getElementById(`actions-${stage.id}`);
    const skipBtn = actionsEl?.querySelector(".btn-skip");
    if (skipBtn) {
      skipBtn.style.display = data.isNewData === false ? "" : "none";
    }

    // Show cancel button
    const cancelBtn = actionsEl?.querySelector(".btn-cancel-edit");
    if (cancelBtn) cancelBtn.style.display = "";

    // Enable inject button
    const injectBtn = actionsEl?.querySelector(".btn-inject");
    if (injectBtn) injectBtn.disabled = false;

    addLog("success", "Draft ready for editing.");
    stage1ShowEditor(stage, "web");
  } catch (err) {
    stage.status = "error";
    updateStageUI(stage);
    addLog("error", `Error: ${err.message}`);
  }
}

async function stage1ScrapeFirebase(stage) {
  stage.status = "running";
  updateStageUI(stage);
  addLog("info", "Stage 1: Loading current data from Firebase...");

  try {
    const response = await fetch("/api/tbill/invitations/firebase-source");
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    stage.draftData = data;
    stage.status = "preview-ready";
    updateStageUI(stage);

    const actionsEl = document.getElementById(`actions-${stage.id}`);
    const cancelBtn = actionsEl?.querySelector(".btn-cancel-edit");
    if (cancelBtn) cancelBtn.style.display = "";

    const injectBtn = actionsEl?.querySelector(".btn-inject");
    if (injectBtn) injectBtn.disabled = false;

    addLog("success", "Firebase data loaded for editing.");
    stage1ShowEditor(stage, "firebase");
  } catch (err) {
    stage.status = "error";
    updateStageUI(stage);
    addLog("error", `Error: ${err.message}`);
  }
}

function stage1ShowEditor(stage, source) {
  const draft = stage.draftData?.draft;
  if (!draft) {
    showPreview(stage, `<div style="color:var(--muted);">No draft data available from this source.</div>`);
    return;
  }

  const sourceBadge = source === "web"
    ? '<span class="source-badge web">🌐 Web Source</span>'
    : '<span class="source-badge firebase">🔥 Firebase Source</span>';

  const html = `
    ${sourceBadge}
    <div class="edit-field">
      <label>Tender Number</label>
      <input type="text" id="inv-tenderNumber" value="${escapeHtml(draft.tenderNumber || "")}" />
    </div>
    <div class="edit-field">
      <label>Bid Submission Deadline</label>
      <input type="text" id="inv-deadline" value="${escapeHtml(draft.bidSubmissionDeadlineString || "")}" />
    </div>
    <div class="edit-field">
      <label>Settlement Date</label>
      <input type="text" id="inv-settlement" value="${escapeHtml(draft.settlementDate || "")}" />
    </div>
    <div class="edit-field">
      <label>PDF URL</label>
      <input type="text" id="inv-pdfUrl" value="${escapeHtml(draft.pdfUrl || "")}" />
    </div>
  `;

  showPreview(stage, html);
  addLog("info", `Editor ready. Edit fields above, then click Inject.`);
}

async function stage1Inject(stage) {
  const tenderNumber = document.getElementById("inv-tenderNumber")?.value?.trim();
  const deadline = document.getElementById("inv-deadline")?.value?.trim();
  const settlement = document.getElementById("inv-settlement")?.value?.trim();
  const pdfUrl = document.getElementById("inv-pdfUrl")?.value?.trim();

  if (!tenderNumber) {
    addLog("warn", "Tender number is required.");
    return;
  }
  if (!deadline) {
    addLog("warn", "Bid submission deadline is required.");
    return;
  }
  if (!settlement) {
    addLog("warn", "Settlement date is required.");
    return;
  }

  const payload = {
    draft: {
      tenderNumber,
      bidSubmissionDeadlineString: deadline,
      settlementDate: settlement,
    },
  };
  if (pdfUrl) payload.draft.pdfUrl = pdfUrl;

  stage.status = "running";
  updateStageUI(stage);
  addLog("warn", "Injecting invitation data to Firestore...");

  try {
    const response = await fetch("/api/tbill/invitations/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const result = await response.json();

    if (result.error) {
      throw new Error(result.error);
    }

    stage.status = "completed";
    stage.draftData = null;
    updateStageUI(stage);
    hidePreview(stage);

    // Hide cancel button
    const actionsEl = document.getElementById(`actions-${stage.id}`);
    const cancelBtn = actionsEl?.querySelector(".btn-cancel-edit");
    if (cancelBtn) cancelBtn.style.display = "none";

    addLog("success", "Inject complete.");
  } catch (err) {
    stage.status = "error";
    updateStageUI(stage);
    addLog("error", `Error: ${err.message}`);
  }
}

function stage1Cancel(stage) {
  stage.status = "not-started";
  stage.draftData = null;
  updateStageUI(stage);
  hidePreview(stage);

  const actionsEl = document.getElementById(`actions-${stage.id}`);
  const cancelBtn = actionsEl?.querySelector(".btn-cancel-edit");
  if (cancelBtn) cancelBtn.style.display = "none";
  const injectBtn = actionsEl?.querySelector(".btn-inject");
  if (injectBtn) injectBtn.disabled = true;
  const skipBtn = actionsEl?.querySelector(".btn-skip");
  if (skipBtn) skipBtn.style.display = "none";

  addLog("info", "Stage 1 cancelled/reset.");
}

// ========== Stage 2: Yield Rates — Dual Source (Web / Firebase) ==========

async function stage2ScrapeWeb(stage) {
  stage.status = "running";
  updateStageUI(stage);
  addLog("info", "Stage 2: Scraping yield rates from BoZ website...");

  try {
    const response = await fetch("/api/tbill/yields/scrape-draft");
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    stage.draftData = data;
    stage.status = "preview-ready";
    updateStageUI(stage);

    const actionsEl = document.getElementById(`actions-${stage.id}`);
    const skipBtn = actionsEl?.querySelector(".btn-skip");
    if (skipBtn) {
      skipBtn.style.display = data.isNewData === false ? "" : "none";
    }

    const cancelBtn = actionsEl?.querySelector(".btn-cancel-edit");
    if (cancelBtn) cancelBtn.style.display = "";

    const injectBtn = actionsEl?.querySelector(".btn-inject");
    if (injectBtn) injectBtn.disabled = false;

    addLog("success", "Yield draft ready for editing.");
    stage2ShowEditor(stage, "web");
  } catch (err) {
    stage.status = "error";
    updateStageUI(stage);
    addLog("error", `Error: ${err.message}`);
  }
}

async function stage2ScrapeFirebase(stage) {
  stage.status = "running";
  updateStageUI(stage);
  addLog("info", "Stage 2: Loading current yield data from Firebase...");

  try {
    const response = await fetch("/api/tbill/yields/firebase-source");
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    stage.draftData = data;
    stage.status = "preview-ready";
    updateStageUI(stage);

    const actionsEl = document.getElementById(`actions-${stage.id}`);
    const cancelBtn = actionsEl?.querySelector(".btn-cancel-edit");
    if (cancelBtn) cancelBtn.style.display = "";

    const injectBtn = actionsEl?.querySelector(".btn-inject");
    if (injectBtn) injectBtn.disabled = false;

    addLog("success", "Firebase yield data loaded for editing.");
    stage2ShowEditor(stage, "firebase");
  } catch (err) {
    stage.status = "error";
    updateStageUI(stage);
    addLog("error", `Error: ${err.message}`);
  }
}

function stage2ShowEditor(stage, source) {
  const draft = stage.draftData?.draft;
  if (!draft) {
    showPreview(stage, `<div style="color:var(--muted);">No yield data available from this source.</div>`);
    return;
  }

  const sourceBadge = source === "web"
    ? '<span class="source-badge web">🌐 Web Source</span>'
    : '<span class="source-badge firebase">🔥 Firebase Source</span>';

  const tbillData = draft.tbill_data || [];

  let rowsHtml = '';
  if (tbillData.length > 0) {
    rowsHtml = `
      <div class="yield-edit-header">
        <span>Tenure</span>
        <span>ISIN</span>
        <span>Discount Rate</span>
        <span>Yield</span>
        <span>Change</span>
      </div>
      <div id="yield-rows-container">
        ${tbillData.map((item, idx) => `
          <div class="yield-edit-row" data-idx="${idx}">
            <input type="text" class="yield-tenure" value="${escapeHtml(item.tenure || '')}" placeholder="e.g. 91-Day" />
            <input type="text" class="yield-isin" value="${escapeHtml(item.isin || '')}" placeholder="ISIN" />
            <input type="number" step="any" class="yield-discount" value="${item.discount_rate ?? ''}" placeholder="0.00" />
            <input type="number" step="any" class="yield-yield" value="${item.yield ?? ''}" placeholder="0.00" />
            <input type="number" step="any" class="yield-change" value="${item.change ?? ''}" placeholder="0.00" />
          </div>
        `).join('')}
      </div>
    `;
  }

  const html = `
    ${sourceBadge}
    <div class="edit-field">
      <label>Tender Number</label>
      <input type="text" id="yield-tenderNo" value="${escapeHtml(draft.tender_no || '')}" />
    </div>
    ${rowsHtml}
  `;

  showPreview(stage, html);
  addLog("info", "Yield editor ready. Edit fields above, then click Inject.");
}

async function stage2Inject(stage) {
  const tenderNo = document.getElementById("yield-tenderNo")?.value?.trim();
  if (!tenderNo) {
    addLog("warn", "Tender number is required.");
    return;
  }

  // Collect yield rows
  const rowEls = document.querySelectorAll("#yield-rows-container .yield-edit-row");
  const tbillData = [];
  rowEls.forEach((row) => {
    const tenure = row.querySelector(".yield-tenure")?.value?.trim();
    const isin = row.querySelector(".yield-isin")?.value?.trim();
    const discountRate = parseFloat(row.querySelector(".yield-discount")?.value) || 0;
    const yieldVal = parseFloat(row.querySelector(".yield-yield")?.value) || 0;
    const change = parseFloat(row.querySelector(".yield-change")?.value) || 0;

    if (tenure) {
      tbillData.push({ tenure, isin, discount_rate: discountRate, yield: yieldVal, change });
    }
  });

  if (tbillData.length === 0) {
    addLog("warn", "At least one yield data entry is required.");
    return;
  }

  const payload = {
    draft: {
      tender_no: tenderNo,
      tbill_data: tbillData,
    },
  };

  stage.status = "running";
  updateStageUI(stage);
  addLog("warn", "Injecting yield data to Firestore...");

  try {
    const response = await fetch("/api/tbill/yields/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const result = await response.json();

    if (result.error) {
      throw new Error(result.error);
    }

    stage.status = "completed";
    stage.draftData = null;
    updateStageUI(stage);
    hidePreview(stage);

    const actionsEl = document.getElementById(`actions-${stage.id}`);
    const cancelBtn = actionsEl?.querySelector(".btn-cancel-edit");
    if (cancelBtn) cancelBtn.style.display = "none";

    addLog("success", "Yield inject complete.");
  } catch (err) {
    stage.status = "error";
    updateStageUI(stage);
    addLog("error", `Error: ${err.message}`);
  }
}

function stage2Cancel(stage) {
  stage.status = "not-started";
  stage.draftData = null;
  updateStageUI(stage);
  hidePreview(stage);

  const actionsEl = document.getElementById(`actions-${stage.id}`);
  const cancelBtn = actionsEl?.querySelector(".btn-cancel-edit");
  if (cancelBtn) cancelBtn.style.display = "none";
  const injectBtn = actionsEl?.querySelector(".btn-inject");
  if (injectBtn) injectBtn.disabled = true;
  const skipBtn = actionsEl?.querySelector(".btn-skip");
  if (skipBtn) skipBtn.style.display = "none";

  addLog("info", "Stage 2 cancelled/reset.");
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
  else if (msg.includes("running") || msg.includes("scrape") || msg.includes("inspect") || msg.includes("preview")) msgClass = "info";

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
