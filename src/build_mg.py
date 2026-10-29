"""Build Metro Grid from the APU Health Monitor template: sign-in, metro look, live in-browser model, Add a train."""
import json, re, pathlib

HERE = pathlib.Path(__file__).parent
s = (HERE / "template.html").read_text()


def rep(a, b, count=1):
    global s
    n = s.count(a)
    assert n == count, (n, a[:80])
    s = s.replace(a, b)


# ---------------------------------------------------------------- head, fonts, tokens
rep("<title>APU Health Monitor</title>", '<meta charset="utf-8">\n<title>Metro Grid</title>')
rep('    $("toastt").textContent = "Depot notified";', '    $("toastt").textContent = "Depot notified"; $("toastt").style.color = "";')
rep('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">',
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Overpass:wght@400;600;700;800;900&family=Overpass+Mono:wght@400;600&display=swap">')
rep("/* Layout: depot control-room screen.", "/* Metro Grid. Layout: sign-in, then an app bar over three views (network map, depot desk, model); the train monitor opens as a sheet.\n   Type is Overpass, drawn from US highway and transit signage. Line colours double as the brand. Single dark theme by choice.\n   Depot control-room screen.")
rep('''  --display: "Barlow Condensed", "Arial Narrow", sans-serif;
  --body: "Barlow", "Segoe UI", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;''', '''  --l1: #3D7DD8;
  --l2: #D64545;
  --l3: #3FAF6E;
  --l4: #E8902E;
  --display: "Overpass", "Arial Narrow", "Helvetica Neue", sans-serif;
  --body: "Overpass", "Segoe UI", system-ui, sans-serif;
  --mono: "Overpass Mono", ui-monospace, Menlo, monospace;''')
rep("h1, h2, h3 { font-family: var(--display); font-weight: 600; letter-spacing: 0.01em;",
    "h1, h2, h3 { font-family: var(--display); font-weight: 800; letter-spacing: -0.01em;")
rep("h1 { font-size: 30px; line-height: 1.05; }", "h1 { font-size: 30px; line-height: 1.05; font-weight: 900; }")
rep("h2 { font-size: 20px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); font-weight: 600; }",
    "h2 { font-size: 15px; text-transform: uppercase; letter-spacing: 0.09em; color: var(--muted); font-weight: 800; }")
# Overpass is wider than Barlow Condensed: step display sizes down
for a, b in [(".trainbtn b { display: block; font-family: var(--display); font-size: 19px; font-weight: 600; }", ".trainbtn b { display: block; font-family: var(--display); font-size: 17px; font-weight: 800; }"),
             (".pill { font-family: var(--display); font-weight: 700; font-size: 22px;", ".pill { font-family: var(--display); font-weight: 900; font-size: 18px;"),
             (".kpi b { font-family: var(--display); font-size: 24px; font-weight: 600;", ".kpi b { font-family: var(--display); font-size: 21px; font-weight: 900;"),
             (".story b { font-family: var(--display); font-size: 17px; font-weight: 600;", ".story b { font-family: var(--display); font-size: 15.5px; font-weight: 800;"),
             (".moment b { font-family: var(--display); font-size: 18px; font-weight: 600;", ".moment b { font-family: var(--display); font-size: 16px; font-weight: 800;"),
             (".sev { font-family: var(--display); font-size: 40px; font-weight: 600;", ".sev { font-family: var(--display); font-size: 36px; font-weight: 900;"),
             (".tr text { font: 700 14px var(--display);", ".tr text { font: 900 13px var(--display);"),
             (".tcard b { font-family: var(--display); font-size: 20px; font-weight: 600; }", ".tcard b { font-family: var(--display); font-size: 17px; font-weight: 800; }"),
             (".tcard .pill { font-size: 15px; padding: 2px 8px; }", ".tcard .pill { font-size: 13px; padding: 3px 8px 1px; }"),
             (".tile b { font-family: var(--display); font-size: 34px; font-weight: 600;", ".tile b { font-family: var(--display); font-size: 30px; font-weight: 900;"),
             (".alert .h b { font-family: var(--display); font-size: 18px; font-weight: 600; }", ".alert .h b { font-family: var(--display); font-size: 16px; font-weight: 800; }"),
             (".toast b { font-family: var(--display); font-size: 18px; font-weight: 600;", ".toast b { font-family: var(--display); font-size: 16px; font-weight: 900;"),
             (".part text.lbl { font: 600 17px var(--display);", ".part text.lbl { font: 800 15px var(--display);")]:
    rep(a, b)
rep('<path id="L1" class="ln" style="stroke:#4C8DDB"', '<path id="L1" class="ln" style="stroke:var(--l1)"')
rep('<path id="L2" class="ln" style="stroke:#D9534F"', '<path id="L2" class="ln" style="stroke:var(--l2)"')
rep('<path id="L3" class="ln" style="stroke:#4CAF7A"', '<path id="L3" class="ln" style="stroke:var(--l3)"')
rep('<path id="L4" class="ln" style="stroke:#E59A3A"', '<path id="L4" class="ln" style="stroke:var(--l4)"')

NEWCSS = """
/* sign-in */
.login { min-height: 100%; display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); background: var(--bg); }
@media (max-width: 860px) { .login { grid-template-columns: minmax(0, 1fr); } .login .art { min-height: 260px; } }
.login .art { position: relative; overflow: hidden; background: #0A0F13; border-right: 1px solid var(--line); display: grid; align-content: end; padding-block: 40px; padding-left: max(28px, env(safe-area-inset-left, 0px)); padding-right: 28px; }
.login .art svg.map { position: absolute; inset: 0; width: 100%; height: 100%; }
.login .art .word { position: relative; font: 900 clamp(46px, 8vw, 104px)/0.86 var(--display); letter-spacing: -0.035em; text-transform: uppercase; margin: 0; }
.login .art .word span { display: block; }
.login .art .word span + span { color: var(--accent); }
.login .art p { position: relative; color: var(--muted); max-width: 42ch; margin: 18px 0 0; font-size: 16px; }
.login .form { display: grid; align-content: center; padding-block: 40px; padding-left: 28px; padding-right: max(28px, env(safe-area-inset-right, 0px)); }
.login form { width: 100%; max-width: 400px; display: grid; gap: 16px; }
.login form h1 { font-size: 26px; }
.field { display: grid; gap: 6px; font-size: 14px; color: var(--muted); }
.field input, .field select, .modal input, .modal select { font: 600 16px var(--body); color: var(--fg); background: var(--panel2); border: 1.5px solid var(--line); border-radius: 8px; padding: 10px 12px 8px; min-width: 0; width: 100%; }
.field input:focus, .modal input:focus, .modal select:focus { outline: 2px solid var(--accent); outline-offset: 1px; }
.roles { display: grid; gap: 8px; border: 0; padding: 0; margin: 0; }
.roles legend { font-size: 14px; color: var(--muted); margin-bottom: 6px; }
.role { display: grid; grid-template-columns: auto 1fr; gap: 2px 10px; align-items: center; background: var(--panel); border: 1.5px solid var(--line); border-radius: 8px; padding: 10px 12px; cursor: pointer; }
.role:has(input:checked) { border-color: var(--accent); }
.role input { accent-color: var(--accent); width: 18px; height: 18px; grid-row: span 2; }
.role b { font: 800 16px var(--display); }
.role span { font-size: 13px; color: var(--muted); }
.login .btn.primary { font-size: 16px; padding: 12px 14px 10px; }
.status-line { font: 12.5px var(--mono); color: var(--muted); }
/* app bar */
.appbar { background: #0A0F13; border-bottom: 1px solid var(--line); position: sticky; top: env(safe-area-inset-top, 0px); z-index: 20; }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 21; background: #0A0F13; }
.appbar-in { max-width: 1240px; margin: 0 auto; display: flex; flex-wrap: wrap; align-items: center; gap: 10px 16px; padding-block: 10px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.brand { display: flex; align-items: center; gap: 10px; font: 900 21px var(--display); letter-spacing: -0.02em; text-transform: uppercase; }
.brand svg { width: 30px; height: 30px; flex: none; }
.appbar-r { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-left: auto; }
.user { font: 600 13px var(--mono); color: var(--muted); padding: 0 4px; }
.btn.ghost { background: none; }
.pagehead p { margin: 4px 0 0; color: var(--muted); max-width: 70ch; }
/* loader */
.loader { position: fixed; inset: 0; z-index: 60; background: rgba(13, 19, 24, 0.94); display: grid; place-items: center; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.loadbox { width: min(460px, 100%); display: grid; gap: 12px; }
.loadbox b { font: 900 20px var(--display); }
.progress { height: 8px; background: var(--panel2); border-radius: 4px; overflow: hidden; }
.progress i { display: block; height: 100%; width: 0; background: var(--accent); transition: width 0.2s; }
/* modal */
.modal { position: fixed; inset: 0; z-index: 55; background: rgba(5, 8, 10, 0.72); display: grid; place-items: center; overflow-y: auto; padding-block: 24px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.modalbox { width: min(620px, 100%); background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 18px; display: grid; gap: 14px; }
.modalbox h2 { color: var(--fg); font-size: 19px; letter-spacing: 0.02em; }
.modalbox fieldset { border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px 12px; margin: 0; display: grid; gap: 8px; min-width: 0; }
.modalbox legend { font-size: 13px; color: var(--muted); padding: 0 4px; }
.modalbox label { display: grid; gap: 5px; font-size: 13.5px; color: var(--muted); min-width: 0; }
.modalbox label.inline { display: flex; align-items: center; gap: 8px; color: var(--fg); }
.modalbox label.inline input { width: auto; accent-color: var(--accent); }
.grid2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.grid3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
@media (max-width: 540px) { .grid2, .grid3 { grid-template-columns: minmax(0, 1fr); } }
.filerow { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.err { color: var(--alarm); font-size: 14px; margin: 0; }
.acts { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
/* model view */
.modelgrid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px; }
@media (max-width: 920px) { .modelgrid { grid-template-columns: minmax(0, 1fr); } }
svg#arch { width: 100%; height: auto; display: block; margin-top: 10px; }
.facts { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 6px 14px; margin: 12px 0 0; font-size: 14px; }
.facts dt { color: var(--muted); }
.facts dd { margin: 0; font-family: var(--mono); font-size: 13px; }
.agree td b { font: 900 18px var(--display); }
.okmark { color: var(--ok); font-weight: 800; }
.feat { font: 600 12.5px var(--mono); background: var(--panel2); border: 1px solid var(--line); border-radius: 12px; padding: 2px 9px; }
.badge.live { background: var(--ok); }
"""
rep("[hidden] { display: none !important; }", "[hidden] { display: none !important; }" + NEWCSS)

# ---------------------------------------------------------------- HTML
LOGO = '''<svg viewBox="0 0 32 32" aria-hidden="true"><rect x="1" y="1" width="30" height="30" rx="8" fill="#141C23" stroke="#2A3743" stroke-width="2"/><path d="M4 16H28" stroke="var(--l1)" stroke-width="4"/><path d="M16 4V28" stroke="var(--l2)" stroke-width="4"/><path d="M7 25L25 7" stroke="var(--l3)" stroke-width="4"/><circle cx="16" cy="16" r="4.5" fill="#E4EBF0" stroke="#0D1318" stroke-width="2"/></svg>'''

LOGIN = f'''<main class="login" id="login">
  <div class="art">
    <svg class="map" viewBox="0 0 600 700" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <g fill="none" stroke-width="14" stroke-linecap="round" stroke-linejoin="round" opacity="0.9">
        <path d="M-20 120 L180 120 L300 240 L620 240" stroke="var(--l1)"/>
        <path d="M300 -20 L300 720" stroke="var(--l2)"/>
        <path d="M-20 520 L120 520 L300 340 L420 340 L620 140" stroke="var(--l3)"/>
        <path d="M180 -20 L180 120 M300 440 L460 600 L620 600" stroke="var(--l4)"/>
      </g>
      <g fill="#0A0F13" stroke="#E4EBF0" stroke-width="5">
        <circle cx="180" cy="120" r="11"/><circle cx="300" cy="240" r="13"/><circle cx="300" cy="340" r="13"/><circle cx="420" cy="340" r="9"/><circle cx="120" cy="520" r="9"/><circle cx="460" cy="600" r="9"/><circle cx="300" cy="440" r="9"/>
      </g>
      <rect x="0" y="380" width="600" height="320" fill="url(#fade)"/>
      <defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0A0F13" stop-opacity="0"/><stop offset="0.7" stop-color="#0A0F13"/></linearGradient></defs>
    </svg>
    <h1 class="word"><span>Metro</span><span>Grid</span></h1>
    <p>Early warning for metro air compressors. A model trained on healthy days watches every train and tells the depot when one starts to drift.</p>
  </div>
  <div class="form">
    <form id="loginform" autocomplete="off">
      <div class="brand">{LOGO}<span>Metro Grid</span></div>
      <h1>Sign in to the depot console</h1>
      <label class="field" for="lname">Your name<input id="lname" name="lname" required maxlength="40" placeholder="e.g. Isha"></label>
      <fieldset class="roles">
        <legend>Sign in as</legend>
        <label class="role"><input type="radio" name="role" value="manager" checked><b>Depot manager</b><span>Sees every alert and books overnight repairs.</span></label>
        <label class="role"><input type="radio" name="role" value="operator"><b>Operator</b><span>Watches the network and acknowledges alerts.</span></label>
      </fieldset>
      <button class="btn primary" type="submit">Enter Metro Grid</button>
      <p class="note" style="margin:0">Demo sign-in for the FML mini-project: there is no password, and your name stays in this browser.</p>
      <p class="status-line" id="loadline">Starting the model…</p>
    </form>
  </div>
</main>

<div id="app" hidden>
<div class="appbar"><div class="appbar-in">
  <div class="brand">{LOGO}<span>Metro Grid</span></div>
  <div class="tabs" role="tablist" aria-label="Views">
    <button class="tab" role="tab" id="tab-network" aria-selected="true" aria-controls="view-network">Network</button>
    <button class="tab" role="tab" id="tab-depot" aria-selected="false" aria-controls="view-depot">Depot desk <span class="badge" id="badge" hidden>0</span></button>
    <button class="tab" role="tab" id="tab-model" aria-selected="false" aria-controls="view-model">Model</button>
  </div>
  <div class="appbar-r">
    <button class="btn" id="netplay" aria-pressed="true">Pause replay</button>
    <button class="btn primary" id="addbtn">+ Add a train</button>
    <span class="user" id="userchip"></span>
    <button class="btn ghost" id="signout">Sign out</button>
  </div>
</div></div>
<div class="wrap" id="netpage">
  <div class="pagehead"><h1 id="pagetitle">Network</h1><p id="pagesub"></p></div>'''

old_head = s[s.index('<div class="wrap" id="netpage">'):s.index('  <div class="netgrid" id="view-network"')]
rep(old_head, LOGIN + "\n")

MODELVIEW = '''
  <div id="view-model" role="tabpanel" aria-labelledby="tab-model" hidden>
    <div class="modelgrid">
      <section class="panel">
        <h2>The model</h2>
        <svg id="arch" viewBox="0 0 640 250" role="img" aria-label="Autoencoder: 14 inputs, hidden layers of 8, 4 and 8, 14 outputs"></svg>
        <p class="note" style="font-size:14px;color:var(--fg)">An autoencoder learns to rebuild the 14 physics features of a healthy compressor. It was trained only on Train A's healthy minutes, so it has never seen a failure. When a compressor starts behaving unlike its healthy self, the rebuild error grows. The error is smoothed over an hour, compared with the train's own healthy calibration minutes to give the health index, and turned into an alarm only if it stays high.</p>
        <dl class="facts" id="facts"></dl>
      </section>
      <section class="panel">
        <h2>Does the browser match the notebook?</h2>
        <p class="note" style="font-size:14px">This page runs the model itself. Every minute below was scored twice, once by the notebook in Colab and once here, and the two are compared.</p>
        <div class="tblwrap" style="max-height:none"><table class="tbl agree" id="agree"></table></div>
        <h2 style="margin-top:16px">Inputs</h2>
        <div class="chips" id="featchips"></div>
      </section>
    </div>
  </div>
'''
rep('''  </div>
</div>

<div class="toast"''', "  </div>\n" + MODELVIEW + '''</div>
</div>

<div class="toast"''')

ADDMODAL = '''
<div class="loader" id="loader" hidden><div class="loadbox"><b id="loadtitle">Running the model</b><div class="progress"><i id="loadbar"></i></div><span class="note" id="loadmsg"></span></div></div>

<div class="modal" id="addmodal" hidden role="dialog" aria-modal="true" aria-labelledby="addtitle">
  <form class="modalbox" id="addform" novalidate>
    <h2 id="addtitle">Add a train</h2>
    <p class="note" style="margin:0;font-size:14px">Load the per-minute feature file for a train, made in Colab by the notebook's <span class="mono">export_train()</span>. The model runs here in your browser and the train joins the network.</p>
    <div class="filerow">
      <input type="file" id="addfile" accept=".csv,.gz,.csv.gz" style="max-width:100%">
      <button type="button" class="btn" id="addsample">Use a sample file</button>
    </div>
    <span class="note" id="addfilename" style="margin:0">No file chosen.</span>
    <div class="grid2">
      <label>Train name<input id="addname" value="Train C" maxlength="20" required></label>
      <label>Runs on<select id="addline"><option value="L3">Green line</option><option value="L4">Orange line</option><option value="L1">Blue line</option><option value="L2">Red line</option></select></label>
    </div>
    <fieldset>
      <legend>Healthy periods the model calibrates on</legend>
      <label class="inline"><input type="radio" name="per" value="file" checked> Use the periods marked in the file</label>
      <label class="inline"><input type="radio" name="per" value="dates"> Set the dates myself</label>
      <div class="grid3" id="perdates" hidden>
        <label>Fit from<input type="date" id="fitfrom"></label>
        <label>Fit until<input type="date" id="fitto"></label>
        <label>Calibrate until<input type="date" id="calto"></label>
      </div>
    </fieldset>
    <fieldset>
      <legend>Reported failure (optional)</legend>
      <div class="grid3">
        <label>Start<input type="datetime-local" id="evstart"></label>
        <label>End<input type="datetime-local" id="evend"></label>
        <label>Kind<input id="evkind" placeholder="air leak" maxlength="20"></label>
      </div>
    </fieldset>
    <div id="addprog" hidden style="display:grid;gap:6px"><div class="progress"><i id="addbar"></i></div><span class="note" id="addmsg" style="margin:0"></span></div>
    <p class="err" id="adderr" hidden></p>
    <div class="acts"><button type="button" class="btn" id="addcancel">Cancel</button><button class="btn primary" type="submit" id="addrun">Run the model</button></div>
  </form>
</div>
'''
rep('<div class="sheet" id="sheet" hidden>', ADDMODAL + '\n<div class="sheet" id="sheet" hidden>')

rep('''    <div class="trains" role="group" aria-label="Choose a train">
      <button class="trainbtn" id="btnA" aria-pressed="true"><b>Train A</b><span>MetroPT-3 · Feb–Sep 2020 · 4 air leaks</span></button>
      <button class="trainbtn" id="btnB" aria-pressed="false"><b>Train B</b><span>MetroPT2 · Apr–Jul 2022 · air + oil leak</span></button>
    </div>''', '''    <div class="trains" id="trainbtns" role="group" aria-label="Choose a train"></div>''')
rep("<p>Replay of the early-warning model on real Porto Metro compressor data. Pick a train, play the recording, and watch the model classify each moment as healthy, watch, alarm or sensor check.</p>",
    "<p id=\"monsub\">The model's verdict for every minute of the recording, computed in this browser. Play the recording and watch it classify each moment as healthy, watch, alarm or sensor check.</p>")
rep('''    <p>Data: the per-minute export from section 14 of the project notebook (Colab run, 22 Oct 2026), sampled every 5 minutes. The model is the autoencoder on the 14 physics features, fitted only on Train A's healthy period (1 Feb to 15 Mar 2020). On Train B it runs as a model the train has never seen.</p>''',
    '''    <p id="foot1">Data: the per-minute physics features exported by the project notebook. The model (an autoencoder on the 14 physics features, fitted only on Train A's healthy period, 1 Feb to 15 Mar 2020) runs in this browser; the monitor shows every fifth minute. On Train B it runs as a model the train has never seen.</p>''')
rep("Schematic network, not to scale. The datasets do not record which line each train ran on, so positions are illustrative. The colour of Trains A and B is the model's real verdict, replayed from the recording at 1 hour per second.",
    "Schematic network, not to scale. The datasets do not record which line each train ran on, so positions are illustrative. Each train's colour is the model's verdict on its real recording, played back at 1 hour per second.")

# ---------------------------------------------------------------- JS
rep('<script>\nconst DATA = __DATA__;\n', '<script type="text/plain" id="engine-src">\n__ENGINE__\n</script>\n<script>\n__ENGINE__\n</script>\n<script>\nconst DATA = __DATA__;\nconst MODEL = __MODEL__;\n')
rep("Train A's recording reaches its alarm at 04:11 on 15 July 2020", "Train A's recording reaches its alarm at 04:09 on 15 July 2020")
rep("const NICE = {", "function startApp(LIVE, AGREE, USER) {\nconst NICE = {")
rep('The alarm switches on at 04:11 on 15 July', 'The alarm switches on at 04:09 on 15 July')
rep("That model is in the report's cross-dataset results, not in this replay.", "That model is in the report's cross-dataset results, not on this page.")
rep('''const U = {};
for (const k of ["A", "B"]) {
  const d = DATA.units[k];
  const mins = new Int32Array(d.m.length); let acc = 0;
  for (let j = 0; j < d.m.length; j++) { acc += d.m[j]; mins[j] = acc; }
  U[k] = { ...d, mins, t0ms: Date.parse(d.t0 + "Z"),
    ev: d.events.map((e) => ({ ...e, s: (Date.parse(e.start + "Z") - Date.parse(d.t0 + "Z")) / 60000, e: (Date.parse(e.end + "Z") - Date.parse(d.t0 + "Z")) / 60000 })) };
}''', '''const U = {}, META = {};
function registerUnit(k, d, events, meta) {
  U[k] = { ...d, ev: events.map((e) => ({ ...e, s: (Date.parse(e.start + "Z") - d.t0ms) / 60000, e: (Date.parse(e.end + "Z") - d.t0ms) / 60000 })) };
  META[k] = meta;
}
function fromReplay(k) {                       // fallback: the notebook's saved outputs
  const d = DATA.units[k], mins = new Int32Array(d.m.length); let acc = 0;
  for (let j = 0; j < d.m.length; j++) { acc += d.m[j]; mins[j] = acc; }
  return { ...d, mins, t0ms: Date.parse(d.t0 + "Z") };
}
const BUILTIN = {
  A: { name: "Train A", sub: "MetroPT-3 · Feb–Sep 2020 · 4 air leaks", short: "MetroPT-3 · 2020", label: "TRAIN A · METROPT-3" },
  B: { name: "Train B", sub: "MetroPT2 · Apr–Jul 2022 · air + oil leak", short: "MetroPT2 · 2022", label: "TRAIN B · METROPT2" },
};
for (const k of ["A", "B"]) registerUnit(k, LIVE[k] || fromReplay(k), DATA.units[k].events, BUILTIN[k]);''')

rep('''  $("btnA").setAttribute("aria-pressed", k === "A"); $("btnB").setAttribute("aria-pressed", k === "B");
  $("carlabel").textContent = k === "A" ? "TRAIN A · METROPT-3" : "TRAIN B · METROPT2";
  $("kpis").innerHTML = KPIS[k].map(([v, l]) => `<div class="kpi"><b>${v}</b><span>${l}</span></div>`).join("");''',
'''  renderTrainBtns();
  $("carlabel").textContent = META[k].label;
  $("kpis").innerHTML = (KPIS[k] || unitKpis(k)).map(([v, l]) => `<div class="kpi"><b>${v}</b><span>${l}</span></div>`).join("");''')
rep('''function pickTrain(k) {
  if (state.u === k) return;
  stop();
  const j = MOMENTS.findIndex((m) => m.u === k && !m.inj);
  pickMoment(j);
}''', '''function pickTrain(k) {
  if (state.u === k) return;
  stop();
  const j = MOMENTS.findIndex((m) => m.u === k && !m.inj);
  if (j >= 0) pickMoment(j); else { const tr = NETTRAINS.find((t) => t.id === k); openAt(k, tr ? tr.lo : 0, "Showing the start of this train's highlighted window."); }
}
function renderTrainBtns() {
  $("trainbtns").innerHTML = Object.keys(U).map((k) => `<button class="trainbtn" data-k="${k}" aria-pressed="${k === state.u}"><b>${esc(META[k].name)}</b><span>${esc(META[k].sub)}</span></button>`).join("");
  document.querySelectorAll("#trainbtns .trainbtn").forEach((b) => b.addEventListener("click", () => pickTrain(b.dataset.k)));
}
function unitKpis(k) {
  const d = U[k], n = d.S.length, ok = d.S.reduce((a, v) => a + v, 0), ag = AGREE[k];
  return [[(ag ? ag.rows : n * 5).toLocaleString("en-GB"), "minutes scored by the model"], [String(EPIS.filter((e) => e.k === k).length), "alarms raised"],
    [Math.round((100 * ok) / n) + "%", "minutes with healthy sensors"], ag && ag.compared ? [ag.matchPct, "minutes where the alarm matches the notebook"] : [ag ? ag.calibN.toLocaleString("en-GB") : "–", "healthy calibration minutes"]];
}''')
rep('$("btnA").onclick = () => pickTrain("A"); $("btnB").onclick = () => pickTrain("B");\n', '')

# network map: generic names, slots for new trains
rep('''const FLEETMETA = { A: "MetroPT-3 · 2020", B: "MetroPT2 · 2022" };
''', '')
rep('''<span class="meta">${FLEETMETA[k]} · recorded''', '''<span class="meta">${esc(META[k].short)} · recorded''')
rep('''<div class="top"><b>Train ${k}</b>''', '''<div class="top"><b>${esc(META[k].name)}</b>''')
rep('''  }).join("") + `<p class="note" style="margin:0">Trains C, D and E are shown for context only. The datasets have no sensor data for them.</p>`;''',
'''  }).join("") + (() => { const idle = NETTRAINS.filter((t) => !t.loop).map((t) => t.id); return idle.length ? `<p class="note" style="margin:0">Grey markers (${idle.join(", ")}) are empty slots with no sensor data. Use <b>Add a train</b> to put a real recording on one.</p>` : ""; })();''')
rep('''  $("story").innerHTML = `<b>Train ${k}, ${day}, ${time}.</b>This is the moment''', '''  $("story").innerHTML = `<b>${esc(META[k].name)}, ${day}, ${time}.</b>This is the moment''')

# depot desk: episodes per unit, names, roles
rep('''const EPIS = [];
for (const k of ["A", "B"]) {
  const d = U[k]; let cur = null;
  for (let j = 0; j < d.mins.length; j++) {
    if (!d.A[j]) continue;
    if (cur && d.mins[j] - d.mins[cur.e] <= 60) { cur.e = j; continue; }
    cur = { k, s: j, e: j }; EPIS.push(cur);
  }
}
for (const ep of EPIS) {''', '''const EPIS = [];
function computeEpisodes(k) {
  const d = U[k], mine = []; let cur = null;
  for (let j = 0; j < d.mins.length; j++) {
    if (!d.A[j]) continue;
    if (cur && d.mins[j] - d.mins[cur.e] <= 60) { cur.e = j; continue; }
    cur = { k, s: j, e: j }; mine.push(cur);
  }
  for (const ep of mine) classifyEpisode(ep);
  EPIS.push(...mine);
}
function classifyEpisode(ep) {''')
rep('''    if (ms > e.e && ms <= e.e + 1440) { ep.oc = "after"; ep.txt = `After ${e.id}`; }
  }
}''', '''    if (ms > e.e && ms <= e.e + 1440) { ep.oc = "after"; ep.txt = `After ${e.id}`; }
  }
}
for (const k of ["A", "B"]) computeEpisodes(k);''')
rep('''  return ["A", "B"].map((k) => {''', '''  return Object.keys(U).map((k) => {''')
rep('''    return `Train ${k}: ${E.length} alarms,''', '''    return `${META[k].name}: ${E.length} alarms,''')
rep('''<td>Train ${e.k}</td>''', '''<td>${esc(META[e.k].name)}</td>''')
rep('''<b>Train ${a.k} · ${PARTNAME[a.part]} alarm</b>''', '''<b>${esc(META[a.k].name)} · ${PARTNAME[a.part]} alarm</b>''')
rep('''<b>Train ${a.k} · sensor check</b>''', '''<b>${esc(META[a.k].name)} · sensor check</b>''')
rep('''`Train ${a.k} alarm at ${a.when.split(",")[0]}''', '''`${META[a.k].name} alarm at ${a.when.split(",")[0]}''')
rep('''        ${a.state !== "booked" ? `<button class="btn" data-act="book" data-id="${a.id}">Book overnight repair (${a.night})</button>` : ""}''',
    '''        ${a.state !== "booked" ? `<button class="btn" data-act="book" data-id="${a.id}" ${USER.role === "manager" ? "" : 'disabled title="Only a depot manager can book repairs"'}>Book overnight repair (${a.night})</button>` : ""}''')
rep('''        <div class="chips" id="chips">
          <button class="chip" data-f="all" aria-pressed="true">All</button>
          <button class="chip" data-f="A" aria-pressed="false">Train A</button>
          <button class="chip" data-f="B" aria-pressed="false">Train B</button>
          <button class="chip" data-f="before" aria-pressed="false">Warned before a failure</button>
        </div>''', '''        <div class="chips" id="chips"></div>''')
rep('''document.querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => {
  histFilter = c.dataset.f; document.querySelectorAll(".chip").forEach((x) => x.setAttribute("aria-pressed", x === c)); renderHist();
}));
renderHist();''', '''function renderChips() {
  const opts = [["all", "All"], ...Object.keys(U).map((k) => [k, META[k].name]), ["before", "Warned before a failure"]];
  $("chips").innerHTML = opts.map(([f, l]) => `<button class="chip" data-f="${f}" aria-pressed="${f === histFilter}">${esc(l)}</button>`).join("");
  document.querySelectorAll("#chips .chip").forEach((c) => c.addEventListener("click", () => { histFilter = c.dataset.f; renderChips(); renderHist(); }));
}
renderChips();
renderHist();''')
rep('''function showTab(t) {
  const dep = t === "depot";
  $("view-network").hidden = dep; $("view-depot").hidden = !dep;
  $("tab-network").setAttribute("aria-selected", !dep); $("tab-depot").setAttribute("aria-selected", dep);
  if (dep) $("toast").hidden = true;
  try { history.replaceState(null, "", "#" + (dep ? "depot" : "network")); } catch (e) {}
}
$("tab-network").onclick = () => showTab("network"); $("tab-depot").onclick = () => showTab("depot");
if (location.hash === "#depot") showTab("depot");
function openAt(k, i) {''', '''const TITLES = {
  network: ["Network", "Trains run around the network while the model watches each one's air production unit. Colour is the model's verdict on the train's real recording. Click a train to open its health monitor."],
  depot: ["Depot desk", "Alerts the model sends to the depot, and every alarm it raised across the recordings."],
  model: ["Model", "What runs behind every colour on the map, and proof that this page computes the same answers as the notebook."],
};
function showTab(t) {
  for (const v of ["network", "depot", "model"]) { $("view-" + v).hidden = v !== t; $("tab-" + v).setAttribute("aria-selected", v === t); }
  $("pagetitle").textContent = TITLES[t][0]; $("pagesub").textContent = TITLES[t][1];
  $("netplay").hidden = t !== "network";
  if (t === "depot") $("toast").hidden = true;
  if (t === "model") renderModel();
  try { history.replaceState(null, "", "#" + t); } catch (e) {}
}
for (const v of ["network", "depot", "model"]) $("tab-" + v).onclick = () => showTab(v);
showTab(["#depot", "#model"].includes(location.hash) ? location.hash.slice(1) : "network");
function openAt(k, i, msg) {''')
rep('''  $("story").innerHTML = `<b>Train ${k}, ${day}, ${time}.</b>Opened from the depot desk. Press Play to see what happened next, or pick a demo moment below.`;''',
    '''  $("story").innerHTML = `<b>${esc(META[k].name)}, ${day}, ${time}.</b>${msg || "Opened from the depot desk. Press Play to see what happened next, or pick a demo moment below."}`;''')


# ---------------------------------------------------------------- plain-language copy (v5)
COPY = [
    ("<p>Early warning for metro air compressors. A model trained on healthy days watches every train and tells the depot when one starts to drift.</p>",
     "<p>Every metro train has an air compressor that powers its brakes and doors. Metro Grid watches each one and warns the depot when it starts behaving differently from its healthy self.</p>"),
    ('      <p class="note" style="margin:0">Demo sign-in for the FML mini-project: there is no password, and your name stays in this browser.</p>\n', ""),
    ("Schematic network, not to scale. The datasets do not record which line each train ran on, so positions are illustrative. Each train's colour is the model's verdict on its real recording, played back at 1 hour per second. A train in alarm is held where it is until the alarm clears; a train on watch slows down.",
     "The map is a simplified drawing, and the datasets don't say which line each train ran on, so the routes are just for show. The colours are real: each train replays its actual sensor recording at one hour per second. A train in alarm stops until the alarm clears, and a train on watch slows down."),
    ("Watch: worse than 95% of healthy minutes</span>", "Watch: a bit unusual, keep an eye on it</span>"),
    ("Alarm: the depot would be notified</span>", "Alarm: clearly unusual for 30 minutes, depot alerted</span>"),
    ("Sensor check: data cannot be trusted</span>", "Sensor check: bad sensor readings, model paused</span>"),
    ("No sensor data in the datasets</span>", "Empty slot: no train loaded yet</span>"),
    ("Alerts arrive here the moment a train's recording reaches an alarm or a sensor fault in the replay. The actions are part of the demo and are not sent anywhere.",
     "New alerts appear here as the replay reaches them. Acknowledge one to show you've seen it, or book the train in for a repair that night. This is a demo, so nothing is actually sent."),
    ("Outcome compares each alarm with the reported failure times. Click a row to open that moment in the health monitor.",
     "Outcome says whether a real reported failure happened close to the alarm. Click any row to see that moment inside the train."),
    ("An autoencoder learns to rebuild the 14 physics features of a healthy compressor. It was trained only on Train A's healthy minutes, so it has never seen a failure. When a compressor starts behaving unlike its healthy self, the rebuild error grows. The error is smoothed over an hour, compared with the train's own healthy calibration minutes to give the health index, and turned into an alarm only if it stays high.",
     "The model is an autoencoder: a small neural network that squeezes 14 measurements through a narrow middle layer and tries to rebuild them. We trained it only on minutes when Train A's compressor was healthy, so it gets very good at rebuilding healthy behaviour and bad at anything else. When a compressor starts to leak, the rebuild gets worse. That error, smoothed over an hour, becomes the health index, and a long stretch of high error becomes an alarm."),
    ("This page runs the model itself. Every minute below was scored twice, once by the notebook in Colab and once here, and the two are compared.",
     "The model runs inside this page. To show it is the same model as in our report, every minute was scored twice, once in the Colab notebook and once here, and the answers are compared below."),
    ('<h2 style="margin-top:16px">Inputs</h2>\n        <div class="chips" id="featchips"></div>',
     '<h2 style="margin-top:16px">What the model looks at</h2>\n        <p class="note" style="font-size:14px">Fourteen measurements worked out from the raw sensors every minute. Each one was picked because an air or oil leak changes it.</p>\n        <div id="featchips" style="display:grid;gap:8px;margin-top:8px"></div>'),
    ("Load the per-minute feature file for a train, made in Colab by the notebook's <span class=\"mono\">export_train()</span>. The model runs here in your browser and the train joins the network.",
     "Bring in another train. In Colab, run <span class=\"mono\">export_train()</span> on the train's raw sensor file to get a feature file, then load it here. The model checks every minute right here in your browser, and the train appears on the map."),
    ("<legend>Healthy periods the model calibrates on</legend>", "<legend>When was this train healthy? The model learns what normal looks like from these days.</legend>"),
    ("Use the periods marked in the file", "Use the healthy days saved in the file"),
    ("Set the dates myself", "Pick the dates myself"),
    ("Fit from<input", "Learn normal from<input"), ("Fit until<input", "Learn normal until<input"), ("Calibrate until<input", "Double-check until<input"),
    ("<legend>Reported failure (optional)</legend>", "<legend>Known failure (optional). The depot desk will then show whether the model warned in time.</legend>"),
    ("The model's verdict for every minute of the recording, computed in this browser. Play the recording and watch it classify each moment as healthy, watch, alarm or sensor check.",
     "A look inside one train's air compressor (the APU). Press Play to run through the recording. Parts light up when the model finds something unusual there."),
    ("The three physics features furthest from this train's healthy baseline right now. During a watch or alarm, their parts light up on the diagram.",
     "The three measurements furthest from normal for this train right now. During a watch or alarm, the matching parts light up on the drawing."),
    ("Four real failures cannot show how small a leak each detector can catch, so the notebook stretched real operating episodes in 12 healthy 24-hour windows to mimic a leak of known size. This was used for testing only, never for training.",
     "Train A only had four real failures, which is too few to tell how small a leak each model can catch. So we tested it with pretend leaks. How it works: we took 12 normal days when nothing was wrong. In each day we edited the recording so that, while the compressor was resting, the air pressure fell faster than it really did. That is exactly what a leak looks like, because escaping air makes the pressure drop. The slider sets how fast: the bigger the number, the bigger the leak compared with the normal air loss. At 0× nothing is changed, so any alarm there would be a false one. We then ran each model on the edited days and counted on how many of the 12 days it raised an alarm. These edited days were only used for this test; no model learned from them."),
    ("Injected leak, as a multiple of the normal pressure-loss rate", "Size of the pretend leak, compared with normal air loss"),
    ("Data: the per-minute physics features exported by the project notebook. The model (an autoencoder on the 14 physics features, fitted only on Train A's healthy period, 1 Feb to 15 Mar 2020) runs in this browser; the monitor shows every fifth minute. On Train B it runs as a model the train has never seen.",
     ""),
    ("    <p>Watch: health index below 0.05, which means the compressor is behaving worse than 95% of healthy minutes. Alarm: the notebook's alarm rule (above the 99.5% healthy level for 80% of 30 minutes, blocked during sensor check). Failure times are the reported times from the dataset documentation. The supervised 24-hour classifier is not shown because it scored close to chance.</p>\n",
     ""),
    ('  ok: "Behaving like the healthy period.",', '  ok: "Working the way it did on healthy days.",'),
    ('  watch: "Worse than 95% of healthy minutes, but not yet the sustained deviation needed for an alarm.",', '  watch: "A bit unusual: worse than 95% of healthy minutes, but not for long enough to raise an alarm.",'),
    ('  alarm: "Above the 99.5% healthy level for most of the last 30 minutes. The depot would be notified.",', '  alarm: "Clearly unusual for most of the last 30 minutes. The depot has been alerted.",'),
    ('  sensor: "Sensor readings are frozen or impossible, so the model does not judge this minute.",', '  sensor: "The sensors are giving frozen or impossible readings, so the model is not judging this minute.",'),
    ('  nodata: "Not enough valid history yet to compute the health index.",', '  nodata: "Not enough recent data yet to work out a health index.",'),
    ('  network: ["Network", "Trains run around the network while the model watches each one\'s air production unit. Colour is the model\'s verdict on the train\'s real recording. Click a train to open its health monitor."],',
     '  network: ["Network", "Each marker is a train. Its colour is what the model thinks of that train\'s air compressor: green is fine, yellow needs watching, red means the depot has been alerted and the train is held. Click a train to look inside."],'),
    ('  depot: ["Depot desk", "Alerts the model sends to the depot, and every alarm it raised across the recordings."],',
     '  depot: ["Depot desk", "The depot team\'s screen. Alerts from the model land in the inbox on the left. On the right is every alarm the model raised and whether a real failure followed."],'),
    ('  model: ["Model", "What runs behind every colour on the map, and proof that this page computes the same answers as the notebook."],',
     '  model: ["Model", "How the model decides, what it looks at, and a check that this page gives the same answers as our Python notebook."],'),
]
for a, b in COPY:
    rep(a, b)

# main script end: close startApp and append the new app code
tail = s[s.rindex("requestAnimationFrame(netFrame);\n</script>"):]
APPJS = (HERE / "mg_app.js").read_text()
rep("requestAnimationFrame(netFrame);\n</script>", "requestAnimationFrame(netFrame);\n" + APPJS)

(HERE / "metro_grid_template.html").write_text(s)

# fill placeholders
data = json.loads((HERE / "data.json").read_text())
model = json.loads((HERE / "real" / "model.json").read_text())
model_small = {k: v for k, v in model.items() if k != "units"}   # per-unit calibration is not needed: each train calibrates on its own file
page = (s.replace("__DATA__", json.dumps(data, separators=(",", ":")))
         .replace("__MODEL__", json.dumps(model_small, separators=(",", ":")))
         .replace("__ENGINE__", (HERE / "engine.js").read_text().replace("</script", "<\\/script")))
(HERE / "metro_grid.html").write_text(page)
print("bytes", len(page))
