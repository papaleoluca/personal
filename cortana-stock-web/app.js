const state = {
  pyodide: null,
  processFn: null,
  combineFn: null,
  files: [],
  result: null,
};

const el = {
  dropZone: document.getElementById("drop-zone"),
  fileInput: document.getElementById("file-input"),
  dropZoneText: document.getElementById("drop-zone-text"),
  runBtn: document.getElementById("run-btn"),
  clearBtn: document.getElementById("clear-btn"),
  status: document.getElementById("status"),
  statusText: document.getElementById("status-text"),
  results: document.getElementById("results-section"),
  errorSection: document.getElementById("error-section"),
  errorMessage: document.getElementById("error-message"),
  summaryGrid: document.getElementById("summary-grid"),
  warningsContainer: document.getElementById("warnings-container"),
  downloads: document.getElementById("downloads"),
  tbody: document.getElementById("results-tbody"),
  filterMovers: document.getElementById("filter-movers"),
  searchInput: document.getElementById("search-input"),
  rowCount: document.getElementById("row-count"),
};

async function bootPyodide() {
  try {
    setStatus("Loading Python runtime…", true);
    state.pyodide = await loadPyodide();

    setStatus("Loading redistribution logic…", true);
    const redistributeSource = await fetch("./redistribute.py").then((r) => {
      if (!r.ok) throw new Error(`Failed to load redistribute.py: ${r.status}`);
      return r.text();
    });
    state.pyodide.runPython(redistributeSource);

    setStatus("Loading combine logic…", true);
    const combineSource = await fetch("./combine_exports.py").then((r) => {
      if (!r.ok) throw new Error(`Failed to load combine_exports.py: ${r.status}`);
      return r.text();
    });
    state.pyodide.runPython(combineSource);

    state.processFn = state.pyodide.globals.get("process_csv");
    state.combineFn = state.pyodide.globals.get("combine_raw_exports_web");
    setStatus("Ready. Drop file(s) above.", false);
    updateButtons();
  } catch (err) {
    setStatus("", false);
    showError(`Could not initialize Python: ${err.message}`);
  }
}

function setStatus(text, spinning) {
  el.statusText.textContent = text;
  el.status.style.visibility = text ? "visible" : "hidden";
  el.status.querySelector(".spinner").style.display = spinning ? "block" : "none";
}

function showError(msg) {
  el.errorMessage.textContent = msg;
  el.errorSection.classList.remove("hidden");
}

function clearError() {
  el.errorSection.classList.add("hidden");
  el.errorMessage.textContent = "";
}

function updateButtons() {
  el.runBtn.disabled = !state.files.length || !state.processFn || !state.combineFn;
  el.clearBtn.disabled = !state.files.length;
}

function handleFiles(fileList) {
  const files = Array.from(fileList || []);
  if (!files.length) return;
  const nonCsv = files.filter((f) => !f.name.toLowerCase().endsWith(".csv"));
  if (nonCsv.length) {
    showError(`Please choose .csv files only. Not a CSV: ${nonCsv.map((f) => f.name).join(", ")}`);
    return;
  }
  clearError();
  state.files = files;
  el.dropZone.classList.add("has-file");
  const label = files.length === 1 ? "1 file selected" : `${files.length} files selected`;
  el.dropZoneText.innerHTML = `<span class="file-name">${label}: ${files.map((f) => escapeHtml(f.name)).join(", ")}</span>`;
  updateButtons();
}

function clearFiles() {
  state.files = [];
  state.result = null;
  el.fileInput.value = "";
  el.dropZone.classList.remove("has-file");
  el.dropZoneText.textContent = "Drop one or more stock export files here or click to select";
  el.results.classList.add("hidden");
  clearError();
  updateButtons();
}

el.fileInput.addEventListener("change", (e) => handleFiles(e.target.files));

el.dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  el.dropZone.classList.add("dragging");
});
el.dropZone.addEventListener("dragleave", () => el.dropZone.classList.remove("dragging"));
el.dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  el.dropZone.classList.remove("dragging");
  handleFiles(e.dataTransfer.files);
});

el.clearBtn.addEventListener("click", clearFiles);

el.runBtn.addEventListener("click", async () => {
  if (!state.files.length || !state.processFn || !state.combineFn) return;
  clearError();
  el.runBtn.disabled = true;
  setStatus("Reading file(s)…", true);

  try {
    const decoder = new TextDecoder("utf-8");
    const texts = [];
    for (const f of state.files) {
      const buf = await f.arrayBuffer();
      texts.push(decoder.decode(buf));
    }
    const names = state.files.map((f) => f.name);

    setStatus("Combining file(s)…", true);
    await new Promise((r) => setTimeout(r, 30));  // let the UI update

    const combineProxy = state.combineFn(names, texts);
    const combined = combineProxy.toJs({ dict_converter: Object.fromEntries });
    combineProxy.destroy();

    setStatus("Running redistribution…", true);
    await new Promise((r) => setTimeout(r, 30));

    const proxy = state.processFn(combined.csv_text);
    const jsResult = proxy.toJs({ dict_converter: Object.fromEntries });
    proxy.destroy();

    state.result = jsResult;
    renderResults(jsResult, combined.stats);
    setStatus("Done.", false);
  } catch (err) {
    console.error(err);
    setStatus("", false);
    showError(`Processing failed: ${err.message}`);
  } finally {
    updateButtons();
  }
});

el.filterMovers.addEventListener("change", () => renderTable(state.result));
el.searchInput.addEventListener("input", () => renderTable(state.result));

function renderResults(result, combineStats) {
  const stats = result.stats;

  const shipmentSummary = stats.shipment_summary || [];
  const madridSummary = shipmentSummary.find((s) => s.shop === "Madrid");
  const palmaSummary = shipmentSummary.find((s) => s.shop === "Palma");
  const barcelonaSummary = shipmentSummary.find((s) => s.shop === "Barcelona");

  el.summaryGrid.innerHTML = "";
  addSummary("Files combined", combineStats.files.length);
  addSummary("Input rows", stats.raw_input_rows, `${stats.dropped_zero_rows} zero, ${stats.dropped_duplicate_rows} dup dropped`);
  addSummary("Processed", stats.cleaned_rows);
  addSummary("SKUs to move", stats.skus_with_moves);
  addSummary("Units total", stats.total_units_transferred);
  if (madridSummary) addSummary("Madrid ships", `${madridSummary.units}`, `${madridSummary.lines} lines`);
  if (palmaSummary) addSummary("Palma ships", `${palmaSummary.units}`, `${palmaSummary.lines} lines`);
  if (barcelonaSummary) addSummary("Barcelona ships", `${barcelonaSummary.units}`, `${barcelonaSummary.lines} lines`);

  el.warningsContainer.innerHTML = "";
  const warnings = [];
  if (combineStats.conflicting_duplicate_skus && combineStats.conflicting_duplicate_skus.length) {
    warnings.push({
      title: `${combineStats.conflicting_duplicate_skus.length} duplicate SKU(s) had conflicting stock values across files`,
      detail: "Kept the first file's numbers for each. Verify these are correct.",
      items: combineStats.conflicting_duplicate_skus.slice(0, 5),
    });
  }
  if (combineStats.mismatched_duplicate_skus && combineStats.mismatched_duplicate_skus.length) {
    warnings.push({
      title: `${combineStats.mismatched_duplicate_skus.length} SKU(s) matched across files but title/size differed`,
      detail: "Both rows were kept as distinct entries. Verify this is correct.",
      items: combineStats.mismatched_duplicate_skus.slice(0, 5),
    });
  }
  if (stats.corrupt_sku_rows && stats.corrupt_sku_rows.length) {
    warnings.push({
      title: `${stats.corrupt_sku_rows.length} row(s) with scientific-notation SKUs`,
      detail: "The source spreadsheet mangled long numeric SKUs into '9E+12'-style values. Rows are processed but you should fix the source.",
      items: stats.corrupt_sku_rows.slice(0, 5).map((r) => `Row ${r.input_row}: ${r.title} — SKU=${r.sku}`),
    });
  }
  if (stats.negative_input_rows && stats.negative_input_rows.length) {
    warnings.push({
      title: `${stats.negative_input_rows.length} row(s) with negative stock`,
      detail: "Passed through unchanged.",
      items: stats.negative_input_rows.slice(0, 5).map((r) => `Row ${r.input_row}: ${r.title} — M=${r.m} P=${r.p} B=${r.b}`),
    });
  }
  if (combineStats.identical_duplicate_skus && combineStats.identical_duplicate_skus.length) {
    warnings.push({
      variant: "info",
      title: `${combineStats.identical_duplicate_skus.length} duplicate SKU(s) merged`,
      detail: "Same SKU, title, size, and stock appeared in more than one file. Kept one copy.",
      items: combineStats.identical_duplicate_skus.slice(0, 5),
    });
  }
  warnings.forEach(renderWarning);

  el.downloads.innerHTML = "";
  const baseName = state.files.length === 1 ? state.files[0].name.replace(/\.csv$/i, "") : "combined";
  addDownload(`${baseName}(out).csv`, result.main_csv);
  addDownload(`${baseName} - Madrid envios.csv`, result.shipments.Madrid);
  addDownload(`${baseName} - Palma envios.csv`, result.shipments.Palma);
  addDownload(`${baseName} - Barcelona envios.csv`, result.shipments.Barcelona);

  renderTable(result);
  el.results.classList.remove("hidden");
}

function addSummary(label, value, hint) {
  const div = document.createElement("div");
  div.className = "summary-item";
  div.innerHTML = `
    <div class="summary-label">${escapeHtml(label)}</div>
    <div class="summary-value">${escapeHtml(String(value))}</div>
    ${hint ? `<div class="summary-hint">${escapeHtml(hint)}</div>` : ""}
  `;
  el.summaryGrid.appendChild(div);
}

function renderWarning(w) {
  const div = document.createElement("div");
  div.className = w.variant === "info" ? "warnings info" : "warnings";
  div.innerHTML = `
    <strong>${escapeHtml(w.title)}</strong>
    <div>${escapeHtml(w.detail)}</div>
    ${w.items.length ? `<ul>${w.items.map((i) => `<li>${escapeHtml(i)}</li>`).join("")}</ul>` : ""}
  `;
  el.warningsContainer.appendChild(div);
}

function addDownload(filename, csvText) {
  const btn = document.createElement("button");
  btn.innerHTML = `<span class="download-icon"></span>${escapeHtml(filename)}`;
  btn.addEventListener("click", () => downloadCsv(filename, csvText));
  el.downloads.appendChild(btn);
}

function downloadCsv(filename, csvText) {
  // Prepend UTF-8 BOM so Excel/Numbers open with correct encoding.
  const blob = new Blob(["﻿" + csvText], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function renderTable(result) {
  if (!result) return;
  const query = el.searchInput.value.trim().toLowerCase();
  const onlyMovers = el.filterMovers.checked;

  const rows = result.rows.filter((r) => {
    if (onlyMovers && r.moves === 0) return false;
    if (query) {
      const hay = `${r.title} ${r.sku}`.toLowerCase();
      if (!hay.includes(query)) return false;
    }
    return true;
  });

  const total = result.rows.length;
  el.rowCount.textContent = `${rows.length} of ${total} row${total === 1 ? "" : "s"}`;

  const html = rows.map((r) => {
    const dm = r.final_m - r.m;
    const dp = r.final_p - r.p;
    const db = r.final_b - r.b;
    const transfers = describeTransfers(r);
    return `
      <tr>
        <td class="title" title="${escapeHtml(r.title)}">${escapeHtml(r.title)}</td>
        <td>${escapeHtml(r.size)}</td>
        <td class="sku">${escapeHtml(r.sku)}</td>
        ${flowCell(r.m, r.final_m, dm)}
        ${flowCell(r.p, r.final_p, dp)}
        ${flowCell(r.b, r.final_b, db)}
        <td class="transfers">${transfers}</td>
        <td class="num">${r.moves}</td>
      </tr>
    `;
  }).join("");

  el.tbody.innerHTML = html || `<tr><td colspan="8" style="text-align:center; color: var(--muted); padding: 24px;">No rows match.</td></tr>`;
}

function flowCell(before, after, delta) {
  const arrow = delta === 0 ? "" : `<span class="arrow">→</span> <span class="${deltaClass(delta)}">${after}</span>`;
  const inner = delta === 0
    ? `<span class="delta-zero">${before}</span>`
    : `<span>${before}</span> ${arrow}`;
  return `<td class="num"><span class="flow">${inner}</span></td>`;
}

function deltaClass(delta) {
  if (delta > 0) return "delta-pos";
  if (delta < 0) return "delta-neg";
  return "delta-zero";
}

function describeTransfers(r) {
  const parts = [];
  if (r.mp) parts.push(`M→P:${r.mp}`);
  if (r.mb) parts.push(`M→B:${r.mb}`);
  if (r.bp) parts.push(`B→P:${r.bp}`);
  if (r.bm) parts.push(`B→M:${r.bm}`);
  if (r.pb) parts.push(`P→B:${r.pb}`);
  if (r.pm) parts.push(`P→M:${r.pm}`);
  return parts.map((p) => `<span class="flow-item">${p}</span>`).join(" ") || "—";
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

bootPyodide();
