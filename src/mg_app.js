
// ---------------------------------------------------------------- Metro Grid additions (still inside startApp)
function esc(s) { return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]); }
const nf = (v) => v.toLocaleString("en-GB");

const EXPLAIN = {
  off_decay_rate_60min: "How fast the air pressure falls while the compressor rests, over the last hour. A leak makes it fall faster.",
  off_decay_rate_360min: "The same pressure fall, averaged over six hours, so short blips matter less.",
  decay_cusum: "A running total of how far the pressure fall has crept above normal. Good at catching slow, steady leaks.",
  decay_ewma_z: "A smoothed trend of the pressure fall compared with normal. It climbs as a leak builds up.",
  load_rise_rate_60min: "How quickly pressure rises while the compressor pumps, over the last hour. Slower when air escapes or the pump is worn.",
  load_rise_rate_360min: "The same pumping speed over six hours.",
  duty_loaded_60min: "Share of the last hour the compressor spent pumping. It has to work harder to make up for lost air.",
  duty_loaded_360min: "The same share of time pumping, over six hours.",
  load_cycles_per_h_60min: "How many times an hour the compressor switches on. A leak makes it start more often.",
  load_cycles_per_h_360min: "The same switch-on count, over six hours.",
  refill_minutes_360min: "How long the main air tank takes to fill back up. It takes longer when air is escaping.",
  oil_temp_excess: "How much hotter the oil is than the workload explains. Points to oil or cooling trouble.",
  tp2_tp3_loaded_60min: "Pressure lost on the way through the air dryer while pumping. Rises if the dryer clogs or leaks.",
  tp3_res_gap_60min: "Difference between the control panel's pressure and the main tank's. Grows when air leaks between them.",
};
function renderModel() {
  const sizes = [MODEL.coefs[0].length, ...MODEL.coefs.map((w) => w[0].length)];
  const cols = ["var(--l1)", "var(--l3)", "var(--l4)", "var(--l3)", "var(--l2)"];
  const X = (l) => 40 + (l * 560) / (sizes.length - 1), Y = (l, j) => 22 + ((j + 0.5) * 190) / sizes[l];
  let edges = "", nodes = "";
  for (let l = 0; l < sizes.length - 1; l++)
    for (let a = 0; a < sizes[l]; a++) for (let b = 0; b < sizes[l + 1]; b++)
      edges += `M${X(l)} ${Y(l, a).toFixed(1)}L${X(l + 1)} ${Y(l + 1, b).toFixed(1)}`;
  sizes.forEach((n, l) => { for (let j = 0; j < n; j++) nodes += `<circle cx="${X(l)}" cy="${Y(l, j).toFixed(1)}" r="5.5" fill="#0A0F13" stroke="${cols[l]}" stroke-width="2.5"/>`; });
  const lab = ["14 features in", "8", "4", "8", "14 rebuilt"];
  $("arch").innerHTML = `<path d="${edges}" stroke="#2A3743" stroke-width="0.6" fill="none"/>${nodes}` +
    lab.map((t, l) => `<text x="${X(l)}" y="240" text-anchor="middle" fill="var(--muted)" style="font:700 12.5px var(--display)">${t}</text>`).join("");
  const fp = MODEL.fit_period.map((d) => { const x = new Date(d + "T00:00:00Z"); return `${x.getUTCDate()} ${MON[x.getUTCMonth()]} ${x.getUTCFullYear()}`; });
  const facts = [
    ["Learned from", `Train A's healthy days only, ${fp[0]} to ${fp[1]}. It never saw a failure.`],
    ["Network size", `${sizes.join(" → ")} neurons (${MODEL.activation}), trained for ${MODEL.n_iter} rounds in scikit-learn ${MODEL.sklearn}`],
    ["Error score", `how badly it rebuilds the 14 measurements, smoothed over ${MODEL.smooth_window_min} minutes`],
    ["Health index", "from 1 (as normal as this train's healthy days) down to 0 (more unusual than any healthy minute)"],
    ["Alarm", `error above the top ${((1 - MODEL.alarm_quantile) * 100).toFixed(1)}% of healthy minutes for ${Math.round(MODEL.persist_fraction * MODEL.persist_window_min)} of the last ${MODEL.persist_window_min} minutes, with sensors working`],
    ["Runs in", "your browser. Nothing is sent to a server."],
  ];
  $("facts").innerHTML = facts.map(([a, b]) => `<dt>${a}</dt><dd>${esc(b)}</dd>`).join("");
  const rows = Object.keys(U).map((k) => {
    const a = AGREE[k];
    if (!a) return `<tr><td>${esc(META[k].name)}</td><td colspan="4">Not run here (${esc(LOADERR || "unknown reason")}), so this shows the notebook's saved results.</td></tr>`;
    if (!a.compared) return `<tr><td>${esc(META[k].name)}</td><td class="num">${nf(a.rows)}</td><td colspan="2">File has no notebook values to compare</td><td class="num">${nf(a.jsAlarm)} / –</td></tr>`;
    return `<tr><td>${esc(META[k].name)}</td><td class="num">${nf(a.compared)}</td><td class="num"><b class="okmark">${a.withinPct}</b></td><td class="num">${a.maxd.toFixed(4)}</td><td class="num">${nf(a.jsAlarm)} / ${nf(a.pyAlarm)}</td></tr>`;
  }).join("");
  $("agree").innerHTML = `<thead><tr><th>Train</th><th class="num">Minutes compared</th><th class="num">Health index within 0.005</th><th class="num">Largest gap</th><th class="num">Alarm minutes, browser / notebook</th></tr></thead><tbody>${rows}</tbody>`;
  $("featchips").innerHTML = MODEL.features.map((f) => `<div><b style="font:800 14.5px var(--display)">${esc(NICE[f][0])}</b> <span class="muted" style="font-size:12px">· ${PARTNAME[NICE[f][1]]}</span><div class="note" style="margin:2px 0 0;font-size:13.5px">${esc(EXPLAIN[f])}</div></div>`).join("");
}

// ---- Add a train
let addBuf = null, addLabel = "";
const freeSlots = () => NETTRAINS.filter((t) => !t.loop);
function refreshAddBtn() {
  const n = freeSlots().length;
  $("addbtn").disabled = n === 0;
  $("addbtn").title = n ? `${n} empty slot${n > 1 ? "s" : ""} on the network` : "The network is full: every slot has a train";
}
refreshAddBtn();
function openAdd() {
  const slot = freeSlots()[0]; if (!slot) return;
  $("addname").value = `Train ${slot.id}`;
  $("adderr").hidden = true; $("addprog").hidden = true; $("addrun").disabled = false;
  $("addmodal").hidden = false; document.body.style.overflow = "hidden"; $("addfile").focus();
}
function closeAdd() { $("addmodal").hidden = true; document.body.style.overflow = ""; }
$("addbtn").onclick = openAdd;
$("addcancel").onclick = closeAdd;
$("addmodal").addEventListener("keydown", (e) => { if (e.key === "Escape") closeAdd(); });
$("addfile").addEventListener("change", async () => {
  const f = $("addfile").files[0]; if (!f) return;
  addBuf = await f.arrayBuffer(); addLabel = f.name;
  $("addfilename").textContent = `${f.name} · ${(f.size / 1e6).toFixed(1)} MB`;
});
$("addsample").onclick = async () => {
  $("addfilename").textContent = "Loading the sample…";
  try {
    addBuf = BUFS.B ? BUFS.B.slice(0) : unb64(await (await fetch("data/train_B.gz.b64.txt")).arrayBuffer());
    addLabel = "train_B_features.csv.gz";
    $("addfilename").textContent = "Sample: Train B's real export from the notebook (MetroPT2, 2022), run again as a new train.";
  } catch (e) { $("addfilename").textContent = "Could not load the sample file."; }
};
document.querySelectorAll('input[name="per"]').forEach((r) => r.addEventListener("change", () => { $("perdates").hidden = !document.querySelector('input[name="per"][value="dates"]').checked; }));
function addErr(msg) { $("adderr").textContent = msg; $("adderr").hidden = false; $("addprog").hidden = true; $("addrun").disabled = false; }
const dmin = (s) => Date.parse(s + (s.length === 10 ? "T00:00:00Z" : ":00Z")) / 60000;
$("addform").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("adderr").hidden = true;
  const slot = freeSlots()[0];
  if (!slot) return addErr("Every slot on the network already has a train.");
  if (!addBuf) return addErr("Choose a feature file first, or use the sample.");
  const name = $("addname").value.trim() || `Train ${slot.id}`;
  const opts = {};
  const evs = $("evstart").value, eve = $("evend").value;
  if ((evs && !eve) || (!evs && eve)) return addErr("Give both a start and an end for the reported failure, or leave both empty.");
  if (evs && dmin(eve) <= dmin(evs)) return addErr("The failure must end after it starts.");
  if (evs) opts.exclude = [dmin(evs) - 1440, dmin(eve)];
  if (document.querySelector('input[name="per"][value="dates"]').checked) {
    const a = $("fitfrom").value, b = $("fitto").value, c = $("calto").value;
    if (!a || !b || !c) return addErr("Fill in all three dates, or use the periods marked in the file.");
    if (!(dmin(a) < dmin(b) && dmin(b) < dmin(c))) return addErr("The dates must run in order: fit from, fit until, calibrate until.");
    opts.dates = { fitFrom: dmin(a), fitTo: dmin(b), calTo: dmin(c) };
  }
  $("addrun").disabled = true; $("addprog").hidden = false;
  const prog = (p, msg) => { $("addbar").style.width = (p * 100).toFixed(0) + "%"; $("addmsg").textContent = msg; };
  prog(0.02, "Starting the model");
  let res;
  try { res = await runModel(addBuf.slice(0), opts, prog); } catch (err) { return addErr(err.message || String(err)); }
  const k = slot.id;
  const events = evs ? [{ id: `${k}-E1`, kind: $("evkind").value.trim() || "failure", start: evs + ":00", end: eve + ":00" }] : [];
  const yrs = [res.info.first.slice(0, 4), res.info.last.slice(0, 4)], yr = yrs[0] === yrs[1] ? yrs[0] : yrs.join("–");
  registerUnit(k, res.unit, events, {
    name, sub: `Added by ${USER.name} · ${addLabel} · ${yr}`, short: `Added · ${yr}`, label: `${name.toUpperCase()} · ADDED`,
  });
  AGREE[k] = res.agree;
  computeEpisodes(k);
  // place it on the network: loop around its first alarm, or the day after calibration
  // focus on the reported failure if there is one: first alarm from 24 h before it to its end
  const d = U[k], line = $("addline").value, ev0 = d.ev[0];
  const ai = ev0 ? d.A.findIndex((v, j) => v && d.mins[j] >= ev0.s - 1440 && d.mins[j] <= ev0.e) : d.A.findIndex((v) => v);
  const centre = ai >= 0 ? d.mins[ai] : ev0 ? ev0.s : res.info.calEnd;
  slot.lo = idxAt(k, centre - (ai >= 0 ? 18 * 60 : 6 * 60)); slot.hi = Math.max(slot.lo + 1, idxAt(k, centre + (ai >= 0 ? 6 * 60 : 18 * 60)));
  slot.loop = true; slot.prev = undefined; slot.acc = 0; pos[k] = slot.lo;
  slot.line = line; slot.path = $(line); slot.len = slot.path.getTotalLength(); slot.t = 0.1 + Math.random() * 0.8;
  const g = $("tr-" + k), tag = (name.split(/\s+/).pop() || k).slice(0, 2).toUpperCase();
  g.setAttribute("tabindex", "0"); g.setAttribute("role", "button"); g.setAttribute("aria-label", `Open the health monitor for ${name}`);
  g.querySelector("text").textContent = tag;
  g.addEventListener("click", () => openTrain(k));
  g.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); openTrain(k); } });
  renderChips(); renderHist(); $("histsum").textContent = histSummary(); renderFleet(); refreshAddBtn();
  closeAdd(); addBuf = null; $("addfile").value = ""; $("addfilename").textContent = "No file chosen.";
  showTab("network");
  const nA = EPIS.filter((x) => x.k === k).length;
  $("toastt").textContent = `${name} joined the network`; $("toastt").style.color = "var(--ok)";
  $("toastm").textContent = `The model scored ${nf(res.agree.rows)} minutes in ${(res.agree.ms / 1000).toFixed(1)} s and raised ${nA} alarm${nA === 1 ? "" : "s"}.` +
    (res.agree.compared ? ` It matches the notebook on ${res.agree.withinPct} of minutes.` : "");
  $("toast").hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { $("toast").hidden = true; }, 9000);
});
document.addEventListener("mg-user", renderInbox);
if (!LIVE.A) $("foot1").textContent = `The model couldn't start in this browser (${LOADERR || "unknown reason"}), so you're seeing our notebook's saved results instead. Try reloading the page or using Chrome. Adding a train needs the model, so that button is off for now.`;
if (!LIVE.A) { $("addbtn").disabled = true; $("addbtn").title = "The model could not start in this browser"; }
}

// ---------------------------------------------------------------- outside startApp: loading, model runs, sign-in
const byId = (id) => document.getElementById(id);
const BUFS = {};

// Self-contained so it can run in a worker or, as a fallback, on the page itself.
async function processBuffer(MG, model, feats, regimes, buf, opts, progress) {
  const t0 = performance.now(), u8 = new Uint8Array(buf);
  progress(0.04, "Unpacking the file");
  const text = u8[0] === 0x1f && u8[1] === 0x8b
    ? await new Response(new Blob([u8]).stream().pipeThrough(new DecompressionStream("gzip"))).text()
    : new TextDecoder().decode(u8);
  progress(0.08, "Reading the minutes");
  const fr = MG.frameFromCSV(model, MG.parseCSV(text)), n = fr.t.length;
  if (n < 2880) throw new Error(`The file has only ${n} minutes. The model needs at least two days.`);
  if (opts.exclude || opts.dates) {
    const x = opts.exclude, D = opts.dates;
    for (let i = 0; i < n; i++) {
      const t = fr.t[i], bad = !fr.ok[i] || (x && t >= x[0] && t <= x[1]);
      if (D) { fr.fit[i] = !bad && t >= D.fitFrom && t < D.fitTo ? 1 : 0; fr.calib[i] = !bad && t >= D.fitTo && t < D.calTo ? 1 : 0; }
      else if (bad) { fr.fit[i] = 0; fr.calib[i] = 0; }
    }
  }
  let nfit = 0, ncal = 0, calEnd = fr.t[0];
  for (let i = 0; i < n; i++) { nfit += fr.fit[i] ? 1 : 0; if (fr.calib[i]) { ncal++; calEnd = fr.t[i]; } }
  if (nfit < 1440 || ncal < 1440)
    throw new Error(`The healthy periods are too short: ${nfit.toLocaleString("en-GB")} fit minutes and ${ncal.toLocaleString("en-GB")} calibration minutes. The model needs at least 1,440 of each (one day). ` +
      (opts.dates ? "Choose longer dates." : "Set the dates yourself, or mark them with export_train()."));
  const r = MG.run(model, fr, null, (p) => progress(0.1 + 0.8 * p, "Scoring every minute"));
  progress(0.95, "Comparing with the notebook");
  let compared = 0, within = 0, maxd = 0, jsAlarm = 0, pyAlarm = 0, mismatch = 0;
  for (let i = 0; i < n; i++) {
    jsAlarm += r.alarm[i];
    if (fr.pyAlarm) { const p = fr.pyAlarm[i] ? 1 : 0; pyAlarm += p; if (p !== r.alarm[i]) mismatch++; }
    if (fr.pyHi && Number.isFinite(fr.pyHi[i]) && Number.isFinite(r.hi[i])) {
      compared++; const dd = Math.abs(fr.pyHi[i] - r.hi[i]); if (dd <= 0.005) within++; if (dd > maxd) maxd = dd;
    }
  }
  const pct = (a, b) => (a === b ? "100%" : ((100 * a) / b).toFixed(2) + "%");
  // every fifth minute for the display; an alarm anywhere in the five minutes is kept
  const t0m = fr.t[0], fmap = model.features.map((f) => feats.indexOf(f)), m = Math.ceil(n / 5);
  const unit = { t0: new Date(t0m * 60000).toISOString().slice(0, 19), t0ms: t0m * 60000, mins: new Int32Array(m), R: [], I: [], O: [], G: [], S: [], H: [], A: [], W: [] };
  const r1 = (v, s) => (Number.isFinite(v) ? Math.round(v * s) : null);
  for (let j = 0; j < m; j++) {
    const i = j * 5; let a = 0;
    for (let q = i; q < Math.min(n, i + 5); q++) a |= r.alarm[q];
    unit.mins[j] = Math.round(fr.t[i] - t0m);
    unit.R.push(r1(fr.R[i], 100)); unit.I.push(r1(fr.I[i], 100)); unit.O.push(r1(fr.O[i], 10));
    const g = regimes.indexOf(fr.regime[i]); unit.G.push(g < 0 ? regimes.indexOf("ambiguous") : g);
    unit.S.push(fr.ok[i] ? 1 : 0); unit.H.push(r1(r.hi[i], 1000)); unit.A.push(a);
    const w = r.why[i]; unit.W.push(fmap[Math.floor(w / 196)] * 196 + fmap[Math.floor(w / 14) % 14] * 14 + fmap[w % 14]);
  }
  return {
    unit,
    agree: { rows: n, compared, within, withinPct: compared ? pct(within, compared) : "", maxd, jsAlarm, pyAlarm, mismatch, matchPct: fr.pyAlarm ? pct(n - mismatch, n) : "", calibN: r.calibN, thr: r.thr, ms: performance.now() - t0 },
    info: { first: fr.stamp[0], last: fr.stamp[n - 1], calEnd: calEnd - t0m },
  };
}

let worker = null, jobs = 0, workerOk = () => {};
// Some hosts block background workers without raising an error, so wait for the worker to say hello first
const workerReady = new Promise((res) => { workerOk = res; setTimeout(() => res(false), 4000); });
const pending = {};
try {
  const src = byId("engine-src").textContent + "\n" + processBuffer.toString() +
    `\nself.onmessage = async (e) => { const { id, buf, opts, model, feats, regimes } = e.data;
      try { const r = await processBuffer(MG, model, feats, regimes, buf, opts, (p, msg) => self.postMessage({ id, p, msg }));
        self.postMessage({ id, done: r }); } catch (err) { self.postMessage({ id, error: err.message || String(err) }); } };
    self.postMessage({ ready: true });`;
  worker = new Worker(URL.createObjectURL(new Blob([src], { type: "text/javascript" })));
  worker.onmessage = (e) => {
    if (e.data.ready) { workerOk(true); return; }
    const { id, p, msg, done, error } = e.data, job = pending[id]; if (!job) return;
    if (error) { delete pending[id]; job.reject(new Error(error)); } else if (done) { delete pending[id]; job.resolve(done); } else job.progress(p, msg);
  };
  worker.onerror = () => { workerOk(false); for (const id in pending) { const j = pending[id]; delete pending[id]; j.workerFail(); } };   // e.g. blocked by the host
} catch (e) { worker = null; workerOk(false); }
async function runModel(buf, opts, progress) {
  const onPage = (b) => processBuffer(MG, MODEL, DATA.feats, DATA.regimes, b, opts, progress);   // same code, on the page
  if (worker && !(await workerReady)) { worker.terminate(); worker = null; }
  if (!worker) return onPage(buf);
  const id = ++jobs, spare = buf.slice(0);
  return new Promise((resolve, reject) => {
    pending[id] = { resolve, reject, progress, workerFail: () => { worker = null; onPage(spare).then(resolve, reject); } };
    worker.postMessage({ id, buf, opts, model: MODEL, feats: DATA.feats, regimes: DATA.regimes }, [buf]);
  });
}

async function fetchBuf(url, onBytes) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  if (!res.body) return res.arrayBuffer();
  const total = +res.headers.get("content-length") || 0, reader = res.body.getReader(), parts = []; let got = 0;
  for (;;) { const { done, value } = await reader.read(); if (done) break; parts.push(value); got += value.length; onBytes(got, total); }
  const out = new Uint8Array(got); let o = 0; for (const p of parts) { out.set(p, o); o += p.length; }
  return out.buffer;
}

// The feature files are gzip, stored as base64 text because the page host only serves text and media types
function unb64(buf) {
  const u8 = new Uint8Array(buf);
  if (u8[0] === 0x1f && u8[1] === 0x8b) return buf;
  const bin = atob(new TextDecoder().decode(u8).trim()), out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out.buffer;
}
const LIVE = {}, AGREE = {};
let LOADERR = "";
let loadState = { p: 0, msg: "Starting the model…" }, ready = null;
function setLoad(p, msg) {
  loadState = { p, msg };
  byId("loadline").textContent = msg;
  byId("loadbar").style.width = (p * 100).toFixed(0) + "%"; byId("loadmsg").textContent = msg;
}
async function loadAll() {
  const ks = ["A", "B"];
  try {
    for (let n = 0; n < ks.length; n++) {
      const k = ks[n], base = n / ks.length, span = 1 / ks.length;
      BUFS[k] = unb64(await fetchBuf(`data/train_${k}.gz.b64.txt`, (got, tot) =>
        setLoad(base + span * 0.3 * (tot ? got / tot : 0), `Downloading Train ${k}'s sensor features · ${(got / 1e6).toFixed(1)}${tot ? " of " + (tot / 1e6).toFixed(1) : ""} MB`)));
      const r = await runModel(BUFS[k].slice(0), {}, (p, msg) => setLoad(base + span * (0.3 + 0.7 * p), `Train ${k}: ${msg.toLowerCase()} · ${Math.round(p * 100)}%`));
      LIVE[k] = r.unit; AGREE[k] = r.agree;
    }
    setLoad(1, `Model ready · ${(AGREE.A.rows + AGREE.B.rows).toLocaleString("en-GB")} minutes scored in this browser`);
  } catch (e) {
    for (const k of ks) { delete LIVE[k]; AGREE[k] = null; }
    LOADERR = e && e.message ? e.message : String(e);
    setLoad(1, "The model couldn't start here, so the app will show the notebook's saved results.");
    console.warn(e);
  }
}
ready = loadAll();

const USER = { name: "", role: "manager" };
try { USER.name = localStorage.getItem("mg-name") || ""; USER.role = localStorage.getItem("mg-role") || "manager"; } catch (e) {}
byId("lname").value = USER.name;
const roleInput = document.querySelector(`input[name="role"][value="${USER.role}"]`); if (roleInput) roleInput.checked = true;
let started = false;
byId("loginform").addEventListener("submit", async (e) => {
  e.preventDefault();
  USER.name = byId("lname").value.trim() || "Guest";
  USER.role = document.querySelector('input[name="role"]:checked').value;
  try { localStorage.setItem("mg-name", USER.name); localStorage.setItem("mg-role", USER.role); } catch (err) {}
  byId("userchip").textContent = `${USER.name} · ${USER.role === "manager" ? "Depot manager" : "Operator"}`;
  if (!started) {
    byId("loader").hidden = false; setLoad(loadState.p, loadState.msg);
    await ready;
    byId("loader").hidden = true;
  }
  byId("login").hidden = true; byId("app").hidden = false; window.scrollTo(0, 0);
  if (!started) { started = true; startApp(LIVE, AGREE, USER); }
  else document.dispatchEvent(new CustomEvent("mg-user"));
});
byId("signout").onclick = () => { byId("app").hidden = true; byId("login").hidden = false; byId("sheet").hidden = true; document.body.style.overflow = ""; byId("lname").focus(); };
</script>
