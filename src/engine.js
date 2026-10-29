// Metro Grid model engine: the notebook's health-index pipeline, ported to the browser.
// Steps mirror fit_and_score(): UnitScaler -> autoencoder reconstruction error -> 60-min median
// smoothing -> percentile against healthy calibration -> 30-min persistence alarm, sensor-gated.
const MG = (() => {
  function parseCSV(text) {
    const lines = text.split(/\r?\n/).filter((l) => l.length);
    const head = lines[0].split(",").map((h) => h.trim());
    const cols = {}; head.forEach((h) => (cols[h] = new Array(lines.length - 1)));
    for (let r = 1; r < lines.length; r++) {
      const parts = lines[r].split(",");
      for (let c = 0; c < head.length; c++) cols[head[c]][r - 1] = parts[c] === undefined ? "" : parts[c];
    }
    return { head, cols, n: lines.length - 1 };
  }
  const num = (v) => (v === "" || v === undefined || v === "nan" || v === "NaN" ? NaN : +v);
  const tmin = (s) => Date.parse(s.replace(" ", "T") + (s.length <= 19 ? "Z" : "")) / 60000;

  function median(a) {
    const v = a.filter((x) => Number.isFinite(x)).sort((x, y) => x - y), n = v.length;
    if (!n) return NaN;
    return n % 2 ? v[(n - 1) >> 1] : (v[n / 2 - 1] + v[n / 2]) / 2;
  }
  function quantile(sorted, q) {               // numpy default (linear)
    const n = sorted.length; if (!n) return NaN;
    const p = q * (n - 1), lo = Math.floor(p), hi = Math.min(n - 1, lo + 1);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (p - lo);
  }
  function searchRight(sorted, x) {
    let lo = 0, hi = sorted.length;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (sorted[mid] <= x) lo = mid + 1; else hi = mid; }
    return lo;
  }
  // pandas rolling("<w>min", min_periods) over a time index: window (t - w, t], NaN values skipped
  function rollTime(t, v, w, minp, fn) {
    const out = new Float64Array(t.length).fill(NaN); let start = 0;
    for (let i = 0; i < t.length; i++) {
      while (t[start] <= t[i] - w) start++;
      const win = [];
      for (let j = start; j <= i; j++) if (Number.isFinite(v[j])) win.push(v[j]);
      if (win.length >= minp) out[i] = fn(win);
    }
    return out;
  }
  const mean = (a) => a.reduce((s, x) => s + x, 0) / a.length;

  function fitScaler(X, fitIdx, d) {
    const med = [], mu = [], sd = [], zmed = [], zsd = [];
    for (let c = 0; c < d; c++) {
      const col = fitIdx.map((i) => X[i][c]);
      const m = median(col); med.push(m);
      const filled = col.map((x) => (Number.isFinite(x) ? x : m));
      const mm = mean(filled); mu.push(mm);
      const s = Math.sqrt(mean(filled.map((x) => (x - mm) ** 2)));   // StandardScaler: ddof 0
      sd.push(s === 0 ? 1 : s);
      const fin = col.filter(Number.isFinite), fm = mean(fin);           // pandas .std(): ddof 1, NaN skipped
      zmed.push(m); zsd.push(Math.sqrt(fin.reduce((a, x) => a + (x - fm) ** 2, 0) / Math.max(1, fin.length - 1)));
    }
    return { median: med, mean: mu, scale: sd, zmed, zsd };
  }

  function forward(model, z) {
    let h = z;
    const L = model.coefs.length;
    for (let l = 0; l < L; l++) {
      const W = model.coefs[l], b = model.intercepts[l], out = new Array(b.length);
      for (let j = 0; j < b.length; j++) {
        let s = b[j];
        for (let i = 0; i < h.length; i++) s += h[i] * W[i][j];
        out[j] = l < L - 1 ? (model.activation === "relu" ? Math.max(0, s) : model.activation === "tanh" ? Math.tanh(s) : 1 / (1 + Math.exp(-s))) : s;
      }
      h = out;
    }
    return h;
  }

  // frame: { t:[minutes], X:[[...]], ok:[0/1], fit:[0/1], calib:[0/1] }; stats optional (from model.units[k])
  function run(model, frame, stats, onProgress) {
    const n = frame.t.length, d = model.features.length;
    const fitIdx = []; for (let i = 0; i < n; i++) if (frame.fit[i]) fitIdx.push(i);
    const sc = fitScaler(frame.X, fitIdx.length ? fitIdx : [...Array(n).keys()], d);
    if (stats) { sc.median = stats.median; sc.mean = stats.mean; sc.scale = stats.scale; }
    const raw = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const z = new Array(d);
      for (let c = 0; c < d; c++) {
        const x = Number.isFinite(frame.X[i][c]) ? frame.X[i][c] : sc.median[c];
        z[c] = Math.fround(Math.max(-model.clip, Math.min(model.clip, (x - sc.mean[c]) / sc.scale[c])));
      }
      const y = forward(model, z);
      let e = 0; for (let c = 0; c < d; c++) e += (y[c] - z[c]) ** 2;
      raw[i] = frame.ok[i] ? e / d : NaN;
      if (onProgress && i % 20000 === 0) onProgress(i / n);
    }
    const s = rollTime(frame.t, raw, model.smooth_window_min, model.smooth_min_periods, median);
    let calib;
    if (stats && stats.calib_sorted) calib = stats.calib_sorted;
    else { calib = []; for (let i = 0; i < n; i++) if (frame.calib[i] && Number.isFinite(s[i])) calib.push(s[i]); calib.sort((a, b) => a - b); }
    const thr = stats && stats.threshold !== undefined ? stats.threshold : quantile(calib, model.alarm_quantile);
    const hi = new Float64Array(n).fill(NaN), high = new Float64Array(n).fill(NaN);
    for (let i = 0; i < n; i++) if (Number.isFinite(s[i])) { hi[i] = 1 - searchRight(calib, s[i]) / Math.max(1, calib.length); high[i] = s[i] > thr ? 1 : 0; }
    const pm = rollTime(frame.t, high, model.persist_window_min, model.persist_min_periods, mean);
    const alarm = new Uint8Array(n);
    for (let i = 0; i < n; i++) alarm[i] = pm[i] >= model.persist_fraction && frame.ok[i] ? 1 : 0;
    // "why": three features furthest from the train's own healthy baseline
    const why = new Uint16Array(n);
    for (let i = 0; i < n; i++) {
      const zs = [];
      for (let c = 0; c < d; c++) { const x = frame.X[i][c]; zs.push([Number.isFinite(x) ? Math.abs(x - sc.zmed[c]) / (sc.zsd[c] + 1e-9) : 0, c]); }
      zs.sort((a, b) => b[0] - a[0] || b[1] - a[1]);
      why[i] = zs[0][1] * 196 + zs[1][1] * 14 + zs[2][1];
    }
    return { score: s, hi, alarm, why, thr, calibN: calib.length, fitN: fitIdx.length };
  }

  function frameFromCSV(model, csv) {
    const C = csv.cols, need = [...model.features, "timestamp", "sensor_ok"];
    const missing = need.filter((c) => !(c in C));
    if (missing.length) throw new Error("This file is missing columns the model needs: " + missing.join(", "));
    const n = csv.n, t = new Float64Array(n), X = new Array(n);
    for (let i = 0; i < n; i++) { t[i] = tmin(C.timestamp[i]); X[i] = model.features.map((f) => num(C[f][i])); }
    const col = (k, dflt) => (k in C ? C[k].map((v) => num(v)) : new Array(n).fill(dflt));
    return {
      t, X, ok: col("sensor_ok", 1).map((v) => (v ? 1 : 0)), fit: col("fit", 0), calib: col("calib", 0),
      regime: C.regime || new Array(n).fill("ambiguous"), R: col("Reservoirs", NaN), I: col("Motor_current", NaN), O: col("Oil_temperature", NaN),
      pyHi: "py_hi" in C ? col("py_hi", NaN) : null, pyAlarm: "py_alarm" in C ? col("py_alarm", 0) : null, stamp: C.timestamp,
    };
  }
  return { parseCSV, frameFromCSV, run, quantile, median, tmin };
})();
if (typeof module !== "undefined") module.exports = MG;
