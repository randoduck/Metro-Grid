# Metro Grid

Early warning for metro air compressors (APU), built for our FML mini-project on the MetroPT-3 and MetroPT2 datasets.

Sign in, watch trains move around a schematic network, and see the health-index model's verdict for each one. The autoencoder (trained in the project notebook on Train A's healthy period) runs in the browser on the real per-minute features. The **Model** tab compares the browser's output with the notebook's, minute by minute.

- `index.html`: the app (open it from a web server, not by double-clicking, because it loads the files in `data/`)
- `data/`: per-minute physics features for Trains A and B (gzip, stored as base64 text)
- `src/`: the browser port of the model (`engine.js`), the app code, and the build script

Run locally: `python3 -m http.server` in this folder, then open http://localhost:8000.

Add a train: in the notebook, run `export_train(path, name, fit_start, fit_end, calib_end)` and load the file it writes with **+ Add a train**.
