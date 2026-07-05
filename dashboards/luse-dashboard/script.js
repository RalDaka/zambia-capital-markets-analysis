const API = {
  latest: "/api/latest-values",
  checkDate: "/api/luse/check-date",
  scrape: "/api/luse/scrape-draft",
  ingest: "/api/ingest",
  indexLatest: "/api/luse/index/latest",
  indexScrape: "/api/luse/index/scrape-draft",
  indexIngest: "/api/luse/index/ingest",
  cecaLatest: "/api/luse/ceca/latest",
  cecaScrape: "/api/luse/ceca/scrape-draft",
  cecaIngest: "/api/luse/ceca/ingest",
  notificationPreview: "/api/luse/notifications/preview",
  notificationSend: "/api/luse/notifications/send",
  manualCorrection: "/api/luse/manual-price-correction",
  analyticsRun: "/api/luse/analytics/run"
};

const companies = [
  { symbol: "AECI", name: "AECI", logo: "" },
  { symbol: "ATEL", name: "AIRTEL", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-atel-logo.png" },
  { symbol: "BATZ", name: "BAT", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-batz-logo.png" },
  { symbol: "BATA", name: "BATA", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/0e2b2974-zm-prima-logo.png" },
  { symbol: "CECZ", name: "CEC", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-cec-logo.webp" },
  { symbol: "CECA", name: "CEC AFRICA", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-cec-logo.webp" },
  { symbol: "CHIL", name: "CHILANGA", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/0fed0e0e-zm-chil-logo.png" },
  { symbol: "DCZM", name: "DCZM", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/8d199fba-dotcom-logo.webp" },
  { symbol: "MAFS", name: "MADISON", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-mfin-logo.png" },
  { symbol: "NATB", name: "NATBREW", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-natbrw-logo.png" },
  { symbol: "PUMA", name: "PUMA", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-puma-logo.webp" },
  { symbol: "REIZUSD", name: "REIZ (US CENTS)", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-reiz-logo.webp" },
  { symbol: "SHOP", name: "SHOPRITE", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-shoprt-logo.webp" },
  { symbol: "SCBL", name: "STANCHART", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-scz-logo.png" },
  { symbol: "ZFCO", name: "ZAFFICO", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/8b9ca42d-zm-zfco-logo.png" },
  { symbol: "ZMBF", name: "ZAMBEEF", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-zamb-logo.png" },
  { symbol: "ZSUG", name: "ZAMBIA SUGAR", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-zmsg-logo.webp" },
  { symbol: "ZMRE", name: "ZAMBIARE", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/Gemini_Generated_Image_ew0uvsew0uvsew0u.png" },
  { symbol: "ZABR", name: "ZAMBREW", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-zambrw-logo.png" },
  { symbol: "ZMFA", name: "ZAMEFA", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-zamefa-logo.png" },
  { symbol: "ZNCO", name: "ZANACO", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-zanaco-logo.png" },
  { symbol: "ZCCM", name: "ZCCM", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/zm-zccm-logo.webp" },
  { symbol: "KLRE", name: "KLRE", logo: "https://storage.googleapis.com/mydatakakuleta/logosLuseCompanies/KRL-PLC-Logo-06.-No-Background-scaled.webp" }
].sort((a, b) => a.name.localeCompare(b.name));

const state = {
  rows: new Map(),
  index: {
    latest: null,
    draft: {}
  },
  ceca: {
    latest: null,
    draft: {}
  },
  notification: {
    preview: null
  }
};

const els = {};

document.addEventListener("DOMContentLoaded", () => {
  cacheElements();
  els.marketDate.value = new Date().toISOString().slice(0, 10);
  els.manualPriceDate.value = new Date().toISOString().slice(0, 10);
  initialiseRows();
  populateManualCompanyOptions();
  renderRows();
  bindActions();
  updateReview();
});

function cacheElements() {
  els.marketDate = document.getElementById("marketDate");
  els.sourceMode = document.getElementById("sourceMode");
  els.backfillMode = document.getElementById("backfillMode");
  els.companyRows = document.getElementById("companyRows");
  els.totalCount = document.getElementById("totalCount");
  els.readyCount = document.getElementById("readyCount");
  els.editedCount = document.getElementById("editedCount");
  els.missingCount = document.getElementById("missingCount");
  els.totalValue = document.getElementById("totalValue");
  els.payloadPreview = document.getElementById("payloadPreview");
  els.luseDate = document.getElementById("luseDate");
  els.lastIngestedDate = document.getElementById("lastIngestedDate");
  els.scrapeDecision = document.getElementById("scrapeDecision");
  els.ingestStatus = document.getElementById("ingestStatus");
  els.facebookMoversInput = document.getElementById("facebookMoversInput");
  els.verifyFacebookBtn = document.getElementById("verifyFacebookBtn");
  els.facebookVerificationResults = document.getElementById("facebookVerificationResults");
  els.manualCompanySymbol = document.getElementById("manualCompanySymbol");
  els.manualPriceDate = document.getElementById("manualPriceDate");
  els.manualPrice = document.getElementById("manualPrice");
  els.manualVolume = document.getElementById("manualVolume");
  els.manualValue = document.getElementById("manualValue");
  els.manualCorrectionStatus = document.getElementById("manualCorrectionStatus");
  els.manualCorrectionBtn = document.getElementById("manualCorrectionBtn");
  els.loadIndexBtn = document.getElementById("loadIndexBtn");
  els.scrapeIndexBtn = document.getElementById("scrapeIndexBtn");
  els.ingestIndexBtn = document.getElementById("ingestIndexBtn");
  els.indexLastValue = document.getElementById("indexLastValue");
  els.indexLastDate = document.getElementById("indexLastDate");
  els.indexDraftChange = document.getElementById("indexDraftChange");
  els.indexCurrentValue = document.getElementById("indexCurrentValue");
  els.indexPriceChange = document.getElementById("indexPriceChange");
  els.indexPercentageChange = document.getElementById("indexPercentageChange");
  els.indexTrades = document.getElementById("indexTrades");
  els.indexVolumeTraded = document.getElementById("indexVolumeTraded");
  els.indexValueTraded = document.getElementById("indexValueTraded");
  els.loadCecaBtn = document.getElementById("loadCecaBtn");
  els.scrapeCecaBtn = document.getElementById("scrapeCecaBtn");
  els.ingestCecaBtn = document.getElementById("ingestCecaBtn");
  els.cecaLastPrice = document.getElementById("cecaLastPrice");
  els.cecaLastDate = document.getElementById("cecaLastDate");
  els.cecaNextDate = document.getElementById("cecaNextDate");
  els.cecaPrice = document.getElementById("cecaPrice");
  els.cecaVolume = document.getElementById("cecaVolume");
  els.cecaValue = document.getElementById("cecaValue");
  els.cecaSource = document.getElementById("cecaSource");
  els.cecaChange = document.getElementById("cecaChange");
  els.cecaStatus = document.getElementById("cecaStatus");
  els.previewNotificationBtn = document.getElementById("previewNotificationBtn");
  els.sendNotificationBtn = document.getElementById("sendNotificationBtn");
  els.notificationReportDate = document.getElementById("notificationReportDate");
  els.notificationMoverCount = document.getElementById("notificationMoverCount");
  els.notificationStatus = document.getElementById("notificationStatus");
  els.notificationTitle = document.getElementById("notificationTitle");
  els.notificationPreview = document.getElementById("notificationPreview");
  els.loadLatestBtn = document.getElementById("loadLatestBtn");
  els.checkDateBtn = document.getElementById("checkDateBtn");
  els.scrapeBtn = document.getElementById("scrapeBtn");
  els.clearBtn = document.getElementById("clearBtn");
  els.ingestBtn = document.getElementById("ingestBtn");
  els.runAnalyticsBtn = document.getElementById("runAnalyticsBtn");
  els.analyticsStatus = document.getElementById("analyticsStatus");
  els.analyticsDate = document.getElementById("analyticsDate");
  els.analyticsCount = document.getElementById("analyticsCount");
}

function initialiseRows() {
  companies.forEach((company) => {
    state.rows.set(company.symbol, {
      ...company,
      lastPrice: null,
      lastDate: null,
      price: null,
      volume: null,
      source: "manual",
      edited: false
    });
  });
}

function populateManualCompanyOptions() {
  els.manualCompanySymbol.innerHTML = companies
    .map((company) => `<option value="${company.symbol}">${company.symbol} - ${company.name}</option>`)
    .join("");
}

function renderRows() {
  els.companyRows.innerHTML = "";

  companies.forEach((company) => {
    const rowState = state.rows.get(company.symbol);
    const row = document.createElement("tr");
    row.dataset.symbol = company.symbol;

    row.innerHTML = `
      <td>
        <div class="company">
          <img src="${company.logo || "https://placehold.co/80x80?text=LuSE"}" alt="${company.name} logo">
          <div>
            <b>${company.name}</b>
            <small>${company.symbol}</small>
          </div>
        </div>
      </td>
      <td class="number">
        <span data-last-price>${formatMoney(rowState.lastPrice)}</span>
        <span class="date-note" data-last-date>${formatDate(rowState.lastDate)}</span>
      </td>
      <td>
        <input
          type="number"
          min="0"
          step="0.0001"
          inputmode="decimal"
          value="${rowState.price ?? ""}"
          data-field="price"
          aria-label="${company.name} new price"
        >
      </td>
      <td><span class="change flat" data-price-change>-</span></td>
      <td>
        <input
          type="number"
          min="0"
          step="1"
          inputmode="numeric"
          value="${rowState.volume ?? ""}"
          data-field="volume"
          aria-label="${company.name} volume"
        >
      </td>
      <td class="number" data-value>${formatMoney(getValue(rowState))}</td>
      <td>
        <select data-field="source" aria-label="${company.name} source">
          <option value="manual">Manual</option>
          <option value="latest">Latest</option>
          <option value="scraped">Scraped</option>
        </select>
      </td>
      <td><span class="status unchanged" data-status>Unchanged</span></td>
    `;

    row.querySelector('[data-field="source"]').value = rowState.source;

    row.addEventListener("input", handleRowInput);
    row.addEventListener("change", handleRowInput);
    els.companyRows.appendChild(row);
    updateRowView(company.symbol);
  });
}

function bindActions() {
  els.marketDate.addEventListener("change", updateReview);
  els.backfillMode.addEventListener("change", updateReview);
  getIndexInputs().forEach((input) => {
    input.addEventListener("input", handleIndexInput);
  });
  getCecaInputs().forEach((input) => {
    input.addEventListener("input", handleCecaInput);
  });
  els.sourceMode.addEventListener("change", () => {
    setAllSources(els.sourceMode.value);
    updateReview();
  });
  els.loadIndexBtn.addEventListener("click", loadLatestIndex);
  els.scrapeIndexBtn.addEventListener("click", fetchIndexDraft);
  els.ingestIndexBtn.addEventListener("click", ingestIndex);
  els.loadCecaBtn.addEventListener("click", loadLatestCeca);
  els.scrapeCecaBtn.addEventListener("click", fetchCecaDraft);
  els.ingestCecaBtn.addEventListener("click", ingestCeca);
  els.verifyFacebookBtn.addEventListener("click", verifyFacebookMovers);
  els.manualCorrectionBtn.addEventListener("click", applyManualCorrection);
  els.previewNotificationBtn.addEventListener("click", previewNotification);
  els.sendNotificationBtn.addEventListener("click", sendNotification);
  els.clearBtn.addEventListener("click", clearDraft);
  els.loadLatestBtn.addEventListener("click", loadLatestValues);
  els.checkDateBtn.addEventListener("click", checkLuseDate);
  els.scrapeBtn.addEventListener("click", fetchScrapeDraft);
  els.ingestBtn.addEventListener("click", approveAndIngest);
  els.runAnalyticsBtn.addEventListener("click", runAnalytics);
}

function handleRowInput(event) {
  const row = event.currentTarget;
  const symbol = row.dataset.symbol;
  const field = event.target.dataset.field;
  const rowState = state.rows.get(symbol);

  if (!field || !rowState) {
    return;
  }

  if (field === "price") {
    rowState.price = parseNumber(event.target.value);
  }

  if (field === "volume") {
    rowState.volume = parseInteger(event.target.value);
  }

  if (field === "source") {
    rowState.source = event.target.value;
  }

  rowState.edited = true;
  updateRowView(symbol);
  updateReview();
}

function updateRowView(symbol) {
  const rowState = state.rows.get(symbol);
  const row = els.companyRows.querySelector(`[data-symbol="${symbol}"]`);
  const status = getStatus(rowState);

  row.querySelector("[data-last-price]").textContent = formatMoney(rowState.lastPrice);
  row.querySelector("[data-last-date]").textContent = formatDate(rowState.lastDate);
  updateChangeView(row, rowState);
  row.querySelector("[data-value]").textContent = formatMoney(getValue(rowState));

  const badge = row.querySelector("[data-status]");
  badge.textContent = status.label;
  badge.className = `status ${status.className}`;

  row.classList.toggle("edited", status.className === "edited" || status.className === "ready");
  row.classList.toggle("warning-row", status.className === "missing");
}

function updateChangeView(row, rowState) {
  const changeEl = row.querySelector("[data-price-change]");
  const change = getPriceChange(rowState);

  if (!change) {
    changeEl.textContent = "-";
    changeEl.className = "change flat";
    return;
  }

  const sign = change.amount > 0 ? "+" : "";
  changeEl.textContent = `${sign}${formatMoney(change.amount)} (${sign}${change.percent.toFixed(2)}%)`;

  if (change.amount > 0) {
    changeEl.className = "change up";
  } else if (change.amount < 0) {
    changeEl.className = "change down";
  } else {
    changeEl.className = "change flat";
  }
}

function getPriceChange(rowState) {
  if (!isValidPrice(rowState.lastPrice) || !isValidPrice(rowState.price)) {
    return null;
  }

  const amount = rowState.price - rowState.lastPrice;
  const percent = (amount / rowState.lastPrice) * 100;

  return { amount, percent };
}

function verifyFacebookMovers() {
  const movers = parseFacebookMovers(els.facebookMoversInput.value);
  els.facebookVerificationResults.innerHTML = "";

  if (!movers.length) {
    els.facebookVerificationResults.innerHTML = '<div class="verify-item missing">No Facebook movers found. Use lines like: ZNCO 7.88</div>';
    return;
  }

  movers.forEach((mover) => {
    const company = findCompanyFromMover(mover.symbol);
    const item = document.createElement("div");

    if (!company) {
      item.className = "verify-item missing";
      item.textContent = `${mover.symbol}: not found in company list`;
      els.facebookVerificationResults.appendChild(item);
      return;
    }

    const rowState = state.rows.get(company.symbol);

    if (!isValidPrice(rowState.price)) {
      item.className = "verify-item missing";
      item.textContent = `${company.symbol}: dashboard draft price unavailable. Fetch scrape draft or enter price first.`;
      els.facebookVerificationResults.appendChild(item);
      return;
    }

    const priceDifference = Math.abs(rowState.price - mover.price);
    const matches = priceDifference <= 0.0001;
    const facebookChange = getChangeFromPrice(rowState.lastPrice, mover.price);
    const dashboardChange = getPriceChange(rowState);
    const facebookChangeText = facebookChange ? ` | Facebook change ${formatSignedPercent(facebookChange.percent)}` : "";
    const dashboardChangeText = dashboardChange ? ` | Dashboard change ${formatSignedPercent(dashboardChange.percent)}` : "";
    item.className = `verify-item ${matches ? "match" : "mismatch"}`;
    item.textContent = `${company.symbol}: Facebook price ${formatPrice(mover.price)} | Dashboard price ${formatPrice(rowState.price)}${facebookChangeText}${dashboardChangeText} | ${matches ? "match" : "check"}`;
    els.facebookVerificationResults.appendChild(item);
  });
}

function parseFacebookMovers(text) {
  return text
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const match = line.match(/^([A-Za-z0-9.-]+)\s+([+-]?\d+(?:\.\d+)?)/);

      if (!match) {
        return null;
      }

      return {
        symbol: match[1].trim().toUpperCase(),
        price: Number(match[2])
      };
    })
    .filter(Boolean);
}

function getChangeFromPrice(lastPrice, newPrice) {
  if (!isValidPrice(lastPrice) || !isValidPrice(newPrice)) {
    return null;
  }

  const amount = newPrice - lastPrice;
  const percent = (amount / lastPrice) * 100;
  return { amount, percent };
}

function findCompanyFromMover(name) {
  const normalizedName = normalizeText(name);
  const aliases = {
    ZCCMIH: "ZCCM",
    ZCCM: "ZCCM",
    AIRTEL: "ATEL",
    MADISON: "MAFS",
    ZAFFICO: "ZFCO",
    ZAMBIARE: "ZMRE",
    ZAMBREW: "ZABR",
    ZANACO: "ZNCO",
    ZAMBEEF: "ZMBF",
    STANCHART: "SCBL",
    SHOPRITE: "SHOP",
    NATBREW: "NATB",
    KLRE: "KLRE"
  };
  const aliasSymbol = aliases[normalizedName];

  if (aliasSymbol) {
    return companies.find((company) => company.symbol === aliasSymbol);
  }

  return companies.find((company) => (
    normalizeText(company.symbol) === normalizedName ||
    normalizeText(company.name) === normalizedName
  ));
}

function normalizeText(value) {
  return String(value).toUpperCase().replace(/[^A-Z0-9]/g, "");
}

function formatSignedPercent(value) {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

async function applyManualCorrection() {
  const symbol = els.manualCompanySymbol.value;
  const date = els.manualPriceDate.value;
  const price = parseNumber(els.manualPrice.value);
  const volume = parseInteger(els.manualVolume.value);
  const value = parseNumber(els.manualValue.value);
  const company = companies.find((item) => item.symbol === symbol);

  if (!symbol || !company || !date || !isValidPrice(price)) {
    setIngestStatus("error", "Manual correction requires company, date, and price.");
    return;
  }

  if (!confirm(`Apply ${company.name} price ${formatPrice(price)} for ${date} to history and current company data?`)) {
    return;
  }

  setButtonLoading(els.manualCorrectionBtn, true, "Applying...");
  setIngestStatus("working", `Applying manual correction for ${company.symbol} on ${date}...`);
  els.manualCorrectionStatus.value = "Applying...";

  try {
    const result = await fetchJson(API.manualCorrection, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol,
        companyName: company.name,
        date,
        price,
        volume,
        value
      })
    });

    els.manualCorrectionStatus.value = result.message;
    setIngestStatus("done", result.message);
  } catch (error) {
    els.manualCorrectionStatus.value = "Failed";
    setIngestStatus("error", error.message);
  } finally {
    setButtonLoading(els.manualCorrectionBtn, false, "Apply Correction");
  }
}

function getStatus(rowState) {
  const hasPrice = isValidPrice(rowState.price);
  const hasVolume = isValidVolume(rowState.volume);

  if (!hasPrice || !hasVolume) {
    return { label: "Missing", className: "missing" };
  }

  if (rowState.edited) {
    return { label: "Edited", className: "edited" };
  }

  return { label: "Ready", className: "ready" };
}

function updateReview() {
  let ready = 0;
  let edited = 0;
  let missing = 0;
  let totalValue = 0;

  state.rows.forEach((rowState) => {
    const status = getStatus(rowState);

    if (status.className === "missing") {
      missing += 1;
    } else {
      ready += 1;
      totalValue += getValue(rowState) || 0;
    }

    if (rowState.edited) {
      edited += 1;
    }
  });

  els.totalCount.textContent = companies.length;
  els.readyCount.textContent = ready;
  els.editedCount.textContent = edited;
  els.missingCount.textContent = missing;
  els.totalValue.textContent = formatMoney(totalValue);
  els.payloadPreview.textContent = JSON.stringify(buildPayload(), null, 2);
}

function getIndexInputs() {
  return [
    els.indexCurrentValue,
    els.indexPriceChange,
    els.indexPercentageChange,
    els.indexTrades,
    els.indexVolumeTraded,
    els.indexValueTraded
  ];
}

function handleIndexInput() {
  state.index.draft = readIndexDraft();
  updateIndexView();
}

function readIndexDraft() {
  return {
    currentValue: parseNumber(els.indexCurrentValue.value),
    priceChange: parseNumber(els.indexPriceChange.value),
    percentageChange: parseNumber(els.indexPercentageChange.value),
    trades: parseInteger(els.indexTrades.value),
    volumeTraded: parseNumber(els.indexVolumeTraded.value),
    valueTraded: parseNumber(els.indexValueTraded.value)
  };
}

function applyIndexDraft(indexData) {
  state.index.draft = { ...indexData };
  els.indexCurrentValue.value = indexData.currentValue ?? "";
  els.indexPriceChange.value = indexData.priceChange ?? "";
  els.indexPercentageChange.value = indexData.percentageChange ?? "";
  els.indexTrades.value = indexData.trades ?? "";
  els.indexVolumeTraded.value = indexData.volumeTraded ?? "";
  els.indexValueTraded.value = indexData.valueTraded ?? "";
  updateIndexView();
}

function updateIndexView() {
  const latest = state.index.latest;
  const draft = readIndexDraft();
  const latestValue = parseNumber(latest?.currentValue);
  const draftValue = parseNumber(draft.currentValue);

  els.indexLastValue.textContent = formatMoney(latestValue);
  els.indexLastDate.textContent = latest?.dateOfUpdate || "-";

  if (isValidPrice(latestValue) && isValidPrice(draftValue)) {
    const amount = draftValue - latestValue;
    const percent = (amount / latestValue) * 100;
    const sign = amount > 0 ? "+" : "";
    els.indexDraftChange.textContent = `${sign}${formatMoney(amount)} (${sign}${percent.toFixed(2)}%)`;
  } else {
    els.indexDraftChange.textContent = "-";
  }
}

async function loadLatestIndex() {
  setButtonLoading(els.loadIndexBtn, true, "Loading...");

  try {
    const data = await fetchJson(API.indexLatest);
    state.index.latest = data.indexData;

    if (data.indexData) {
      applyIndexDraft(data.indexData);
    }

    setIngestStatus("done", "Latest LuSE index data loaded from Firebase.");
  } catch (error) {
    setIngestStatus("error", error.message);
  } finally {
    setButtonLoading(els.loadIndexBtn, false, "Load Index Latest");
  }
}

async function fetchIndexDraft() {
  setButtonLoading(els.scrapeIndexBtn, true, "Fetching...");

  try {
    const data = await fetchJson(API.indexScrape);

    if (data.indexData?.dateOfUpdate && !els.backfillMode.checked) {
      els.marketDate.value = data.indexData.dateOfUpdate;
    }

    applyIndexDraft(data.indexData || {});
    setIngestStatus("done", `Index draft loaded for ${data.indexData?.dateOfUpdate || els.marketDate.value}.`);
  } catch (error) {
    setIngestStatus("error", error.message);
  } finally {
    setButtonLoading(els.scrapeIndexBtn, false, "Fetch Index Draft");
  }
}

async function ingestIndex() {
  const indexData = readIndexDraft();
  const marketDate = els.marketDate.value;

  if (!marketDate) {
    setIngestStatus("error", "Select a market date before ingesting index data.");
    return;
  }

  const missingFields = Object.entries(indexData)
    .filter(([, value]) => value === null)
    .map(([key]) => key);

  if (missingFields.length) {
    setIngestStatus("error", `Missing index fields: ${missingFields.join(", ")}.`);
    return;
  }

  if (!confirm(`Ingest LuSE index data for ${marketDate}?`)) {
    return;
  }

  setButtonLoading(els.ingestIndexBtn, true, "Ingesting...");
  setIngestStatus("working", `Ingesting LuSE index data for ${marketDate}...`);

  try {
    const result = await fetchJson(API.indexIngest, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        marketDate,
        allowSpecificDateInjection: els.backfillMode.checked,
        dateMode: els.backfillMode.checked ? "manual_backfill" : "current_market_date",
        indexData
      })
    });

    setIngestStatus(
      "done",
      `Index done for ${result.marketDate}. History added: ${result.historyAdded ? "yes" : "no"}. ` +
      `Current index updated: ${result.currentUpdated ? "yes" : "no"}.`
    );
  } catch (error) {
    setIngestStatus("error", error.message);
  } finally {
    setButtonLoading(els.ingestIndexBtn, false, "Ingest Index");
  }
}

function getCecaInputs() {
  return [
    els.cecaPrice,
    els.cecaVolume,
    els.cecaValue
  ];
}

function readCecaDraft() {
  return {
    price: parseNumber(els.cecaPrice.value),
    volume: parseInteger(els.cecaVolume.value),
    value: parseNumber(els.cecaValue.value),
    source: els.cecaSource.value || "AfricanFinancials"
  };
}

function handleCecaInput() {
  state.ceca.draft = readCecaDraft();
  updateCecaView();
}

function applyCecaDraft(cecaData) {
  state.ceca.draft = { ...cecaData };
  els.cecaPrice.value = cecaData.price ?? "";
  els.cecaVolume.value = cecaData.volume ?? "";
  els.cecaValue.value = cecaData.value ?? "";
  els.cecaSource.value = cecaData.source || "AfricanFinancials";
  updateCecaView();
}

function applyCecaState(syncState) {
  state.ceca.latest = syncState;
  updateCecaView();
}

function updateCecaView() {
  const latest = state.ceca.latest;
  const draft = readCecaDraft();
  const lastPrice = parseNumber(latest?.cecaLastPrice ?? latest?.current?.price);
  const draftPrice = parseNumber(draft.price);

  els.cecaLastPrice.textContent = formatMoney(lastPrice);
  els.cecaLastDate.textContent = latest?.cecaLastDate || "-";
  els.cecaNextDate.textContent = latest?.nextHistoryDate || (latest?.isSynced ? "Synced" : "-");

  if (isValidPrice(lastPrice) && isValidPrice(draftPrice)) {
    const amount = draftPrice - lastPrice;
    const percent = (amount / lastPrice) * 100;
    const sign = amount > 0 ? "+" : "";
    els.cecaChange.value = `${sign}${formatMoney(amount)} (${sign}${percent.toFixed(2)}%)`;
  } else {
    els.cecaChange.value = "";
  }

  if (latest?.isSynced) {
    els.cecaStatus.value = "Already synced with CECZ";
  } else if (latest?.nextHistoryDate) {
    els.cecaStatus.value = `Ready to sync ${latest.nextHistoryDate}`;
  } else {
    els.cecaStatus.value = "Check CECA/CECZ history";
  }
}

async function loadLatestCeca() {
  setButtonLoading(els.loadCecaBtn, true, "Loading...");

  try {
    const data = await fetchJson(API.cecaLatest);
    applyCecaState(data);
    applyCecaDraft({
      price: data.current?.price,
      volume: data.current?.volume,
      value: data.current?.value,
      source: "Firebase"
    });
    setIngestStatus("done", "Latest CECA data loaded from Firebase.");
  } catch (error) {
    setIngestStatus("error", error.message);
  } finally {
    setButtonLoading(els.loadCecaBtn, false, "Load CECA Latest");
  }
}

async function fetchCecaDraft() {
  setButtonLoading(els.scrapeCecaBtn, true, "Fetching...");

  try {
    const data = await fetchJson(API.cecaScrape);
    applyCecaState(data.syncState);
    applyCecaDraft(data.cecaData || {});
    setIngestStatus("done", "CECA draft loaded from AfricanFinancials.");
  } catch (error) {
    setIngestStatus("error", error.message);
  } finally {
    setButtonLoading(els.scrapeCecaBtn, false, "Fetch CECA Draft");
  }
}

async function ingestCeca() {
  const cecaData = readCecaDraft();

  if (!isValidPrice(cecaData.price) || !isValidVolume(cecaData.volume) || cecaData.value === null) {
    setIngestStatus("error", "CECA price, volume, and value are required.");
    return;
  }

  if (!confirm("Ingest CECA current data and sync the next CECA history date?")) {
    return;
  }

  setButtonLoading(els.ingestCecaBtn, true, "Ingesting...");
  setIngestStatus("working", "Ingesting CECA data...");

  try {
    const result = await fetchJson(API.cecaIngest, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cecaData })
    });

    setIngestStatus("done", result.message);
    await loadLatestCeca();
  } catch (error) {
    setIngestStatus("error", error.message);
  } finally {
    setButtonLoading(els.ingestCecaBtn, false, "Ingest CECA");
  }
}

function applyNotificationPreview(preview) {
  state.notification.preview = preview;
  els.notificationReportDate.textContent = preview.reportDate || "-";
  els.notificationMoverCount.textContent = preview.changes?.length ?? 0;
  els.notificationStatus.textContent = preview.alreadySent ? "Already sent" : "Ready";
  els.notificationTitle.value = preview.title || "";
  els.notificationPreview.value = preview.body || "";
}

async function previewNotification() {
  setButtonLoading(els.previewNotificationBtn, true, "Previewing...");

  try {
    const preview = await fetchJson(API.notificationPreview);
    applyNotificationPreview(preview);

    if (preview.alreadySent) {
      setIngestStatus("warning", `Daily notification was already sent for ${preview.reportDate}.`);
    } else {
      setIngestStatus("done", `Notification preview ready for ${preview.reportDate}.`);
    }
  } catch (error) {
    setIngestStatus("error", error.message);
  } finally {
    setButtonLoading(els.previewNotificationBtn, false, "Preview Notification");
  }
}

async function sendNotification() {
  if (!state.notification.preview) {
    setIngestStatus("error", "Preview the notification before sending.");
    return;
  }

  if (state.notification.preview.alreadySent) {
    setIngestStatus("error", `Notification already sent for ${state.notification.preview.reportDate}.`);
    return;
  }

  if (!confirm(`Send daily LuSE movers notification for ${state.notification.preview.reportDate}?`)) {
    return;
  }

  const title = els.notificationTitle.value.trim();
  const body = els.notificationPreview.value.trim();

  if (!title || !body) {
    setIngestStatus("error", "Notification title and body are required.");
    return;
  }

  setButtonLoading(els.sendNotificationBtn, true, "Sending...");
  setIngestStatus("working", "Sending LuSE movers notification...");

  try {
    const result = await fetchJson(API.notificationSend, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        body,
        reportDate: state.notification.preview.reportDate
      })
    });

    setIngestStatus("done", `Notification sent for ${result.reportDate}. Movers sent: ${result.changesSent}.`);
    await previewNotification();
  } catch (error) {
    setIngestStatus("error", error.message);
  } finally {
    setButtonLoading(els.sendNotificationBtn, false, "Send Notification");
  }
}

function buildPayload() {
  const marketDate = els.marketDate.value;
  const companiesPayload = {};

  state.rows.forEach((rowState) => {
    if (!isValidPrice(rowState.price) || !isValidVolume(rowState.volume)) {
      return;
    }

    companiesPayload[rowState.name] = {
      symbol: rowState.symbol,
      companyName: rowState.name,
      price: rowState.price,
      volume: rowState.volume,
      value: getValue(rowState),
      source: rowState.source
    };
  });

  return {
    marketDate,
    sourceMode: els.sourceMode.value,
    dateMode: els.backfillMode.checked ? "manual_backfill" : "current_market_date",
    allowSpecificDateInjection: els.backfillMode.checked,
    status: "pending_ingest",
    productionTargets: {
      currentCompanies: "luse_listed_companies_data/{companyName}",
      historicPrices: "luseCompanyHistoricPrices/{symbol}",
      meta: "system_meta/lusePortfolio"
    },
    companies: companiesPayload
  };
}

async function loadLatestValues() {
  if (!API.latest) {
    alert("Latest-values endpoint is not connected yet. You can still enter values manually.");
    return;
  }

  const data = await fetchJson(API.latest);
  applyIncomingRows(data.companies || {}, "latest");
  els.sourceMode.value = "latest";
  updateReview();
}

async function checkLuseDate() {
  setButtonLoading(els.checkDateBtn, true, "Checking...");

  try {
    const data = await fetchJson(API.checkDate);
    showDateCheck(data);

    if (data.luseDate && !els.backfillMode.checked) {
      els.marketDate.value = data.luseDate;
    }
  } catch (error) {
    els.scrapeDecision.textContent = error.message;
    els.scrapeDecision.className = "bad";
  } finally {
    setButtonLoading(els.checkDateBtn, false, "Check LuSE Date");
  }
}

async function fetchScrapeDraft() {
  if (!API.scrape) {
    alert("Scrape endpoint is not connected yet. This button will autofill rows once the backend exists.");
    return;
  }

  setButtonLoading(els.scrapeBtn, true, "Fetching...");

  try {
    const data = await fetchJson(API.scrape);

    if (data.marketDate && !els.backfillMode.checked) {
      els.marketDate.value = data.marketDate;
    }

    if (data.dateCheck) {
      showDateCheck(data.dateCheck);
    }

    applyIncomingRows(data.companies || {}, "scraped");
    els.sourceMode.value = "scraped";
    updateReview();

    if (data.missingCompanies?.length) {
      setIngestStatus(
        "warning",
        `Scrape draft loaded for ${data.marketDate}, but LuSE did not return: ${data.missingCompanies.join(", ")}.`
      );
    } else {
      setIngestStatus("done", `Scrape draft loaded for ${data.marketDate}. All companies were found.`);
    }
  } catch (error) {
    alert(error.message);
  } finally {
    setButtonLoading(els.scrapeBtn, false, "Fetch Scrape Draft");
  }
}

async function approveAndIngest() {
  const payload = buildPayload();
  const readyCount = Object.keys(payload.companies).length;

  if (!payload.marketDate) {
    alert("Select a market date before ingesting.");
    return;
  }

  if (!readyCount) {
    alert("Enter at least one complete company row before ingesting.");
    return;
  }

  const modeLabel = payload.allowSpecificDateInjection ? "manual backfill" : "market-date ingest";

  if (!confirm(`Prepare ${modeLabel} for ${readyCount} company rows on ${payload.marketDate}?`)) {
    return;
  }

  if (!API.ingest) {
    console.log("Ingest payload:", payload);
    alert("Backend ingest endpoint is not connected yet. Payload printed to console and preview panel.");
    return;
  }

  setIngestStatus("working", `Ingesting ${readyCount} rows for ${payload.marketDate}...`);
  setButtonLoading(els.ingestBtn, true, "Ingesting...");

  try {
    const result = await fetchJson(API.ingest, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    setIngestStatus(
      "done",
      `Done for ${result.marketDate}. History added: ${result.historyAddedCount}. ` +
      `History skipped: ${result.historySkippedCount}. Current docs updated: ${result.currentUpdatedCount}. ` +
      `Meta updated: ${result.metaUpdated ? "yes" : "no"}.`
    );
  } catch (error) {
    setIngestStatus("error", error.message);
  } finally {
    setButtonLoading(els.ingestBtn, false, "Approve & Ingest");
  }
}

async function runAnalytics() {
  if (!confirm("Run company analytics to calculate 1M/3M/6M/1Y percentage changes?")) {
    return;
  }

  setButtonLoading(els.runAnalyticsBtn, true, "Running...");
  setIngestStatus("working", "Running company analytics...");

  try {
    const result = await fetchJson(API.analyticsRun);

    els.analyticsDate.textContent = result.processedDate || "-";
    els.analyticsCount.textContent = result.companiesUpdated ?? 0;

    if (result.status === "skipped") {
      els.analyticsStatus.textContent = "Already up-to-date";
      setIngestStatus("warning", result.message);
    } else {
      els.analyticsStatus.textContent = "Completed";
      setIngestStatus("done", result.message);
    }

    if (result.errors?.length) {
      console.warn("Analytics errors:", result.errors);
    }
  } catch (error) {
    els.analyticsStatus.textContent = "Failed";
    setIngestStatus("error", error.message);
  } finally {
    setButtonLoading(els.runAnalyticsBtn, false, "Run Analytics");
  }
}

function applyIncomingRows(incomingRows, source) {
  Object.entries(incomingRows).forEach(([key, incoming]) => {
    const symbol = incoming.symbol || findSymbolByName(key);
    const rowState = state.rows.get(symbol);

    if (!rowState) {
      return;
    }

    const incomingLastPrice = parseNumber(incoming.lastPrice);

    if (incomingLastPrice !== null) {
      rowState.lastPrice = incomingLastPrice;
    }

    if (incoming.lastDate || incoming.todayDate) {
      rowState.lastDate = incoming.lastDate ?? incoming.todayDate;
    }

    rowState.price = parseNumber(incoming.price);
    rowState.volume = parseInteger(incoming.volume ?? incoming.today_volume);
    rowState.source = source;
    rowState.edited = false;

    const row = els.companyRows.querySelector(`[data-symbol="${symbol}"]`);
    row.querySelector('[data-field="price"]').value = rowState.price ?? "";
    row.querySelector('[data-field="volume"]').value = rowState.volume ?? "";
    row.querySelector('[data-field="source"]').value = source;
    updateRowView(symbol);
  });
}

function setAllSources(source) {
  state.rows.forEach((rowState) => {
    rowState.source = source;
    const row = els.companyRows.querySelector(`[data-symbol="${rowState.symbol}"]`);
    row.querySelector('[data-field="source"]').value = source;
    updateRowView(rowState.symbol);
  });
}

function clearDraft() {
  if (!confirm("Clear all entered prices and volumes?")) {
    return;
  }

  state.rows.forEach((rowState) => {
    rowState.price = null;
    rowState.volume = null;
    rowState.source = "manual";
    rowState.edited = false;

    const row = els.companyRows.querySelector(`[data-symbol="${rowState.symbol}"]`);
    row.querySelector('[data-field="price"]').value = "";
    row.querySelector('[data-field="volume"]').value = "";
    row.querySelector('[data-field="source"]').value = "manual";
    updateRowView(rowState.symbol);
  });

  els.sourceMode.value = "manual";
  updateReview();
}

function showDateCheck(data) {
  els.luseDate.textContent = data.luseDate || "Unavailable";
  els.lastIngestedDate.textContent = data.lastIngestedDate || "Unknown";

  if (data.canScrape) {
    els.scrapeDecision.textContent = "New LuSE date found";
    els.scrapeDecision.className = "good";
    return;
  }

  els.scrapeDecision.textContent = data.message || "No newer LuSE date";
  els.scrapeDecision.className = "hold";
}

function setButtonLoading(button, loading, label) {
  button.disabled = loading;
  button.textContent = label;
}

function setIngestStatus(type, message) {
  els.ingestStatus.className = `ingest-status ${type}`;
  els.ingestStatus.textContent = message;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const error = await response.json();
      message = error.error || message;
    } catch {
      // Keep the generic message when the server does not return JSON.
    }

    throw new Error(message);
  }

  return response.json();
}

function findSymbolByName(name) {
  return companies.find((company) => company.name === name)?.symbol;
}

function getValue(rowState) {
  if (!isValidPrice(rowState.price) || !isValidVolume(rowState.volume)) {
    return null;
  }

  return rowState.price * rowState.volume;
}

function parseNumber(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }

  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function parseInteger(value) {
  const number = parseNumber(value);
  return number === null ? null : Math.trunc(number);
}

function isPositiveNumber(value) {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

function isValidPrice(value) {
  return isPositiveNumber(value);
}

function isValidVolume(value) {
  return typeof value === "number" && Number.isFinite(value) && value >= 0;
}

function formatMoney(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }

  return value.toLocaleString("en-ZM", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

function formatPrice(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }

  return value.toLocaleString("en-ZM", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4
  });
}

function formatDate(value) {
  return value || "-";
}
