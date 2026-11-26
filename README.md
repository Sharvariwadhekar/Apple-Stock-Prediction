# P717 historical forecast lab — team handoff

This package contains the application and its verified forecast artifact. It does not need the ExcelR CSV, development repository, model objects, or model training. Results are historical: the source data ends on 2019-12-30 and the forecast horizon is provisionally 30 trading sessions. These are not current market predictions.

## First-time Windows setup

1. Extract this complete ZIP to a folder you can write to. The `artifacts` folder and forecast JSON are already included; keep them beside `app.py` as extracted.
2. Install 64-bit Python 3.13 and enable the Windows Python launcher (`py`). Internet access is needed once to install dependencies.
3. Open PowerShell in the extracted folder and run:

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

   If `py -3.13` is unavailable, install Python 3.13 and its launcher, then reopen PowerShell. Alternatively use your installed Python 3.13 executable with `-m venv .venv`.
4. Double-click `run_app.bat`. The browser should open to the local app. If it does not, use the local URL shown in the console window.

## Stop and restart

Keep the console window open while using the app. To stop it, press Ctrl+C in that window or close it. To restart, double-click `run_app.bat` again. If dependencies are missing, repeat the pip install command above.

## Artifact and sharing

The included artifact contains the evaluated historical forecasts and actual values. Its expected SHA-256 is `17492C3F1BA3FB9820DB41F80B89FBFE235191E4DFCEDCB7F8CBCFDE4A6F0C04`. Internal sharing with the P717 project team has been approved. This approval does not authorize public publication; do not upload this package, its artifact, the original CSV, or model files to a public repository.
