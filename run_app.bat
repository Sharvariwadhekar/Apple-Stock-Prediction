@echo off
setlocal
cd /d "%~dp0"
if not exist "artifacts\p717_demo_v2.json" (
  echo Missing artifacts\p717_demo_v2.json.
  echo After permission is confirmed, place the separately supplied artifact in the artifacts folder.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv. Follow the first-time setup instructions in README.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -c "import streamlit, pandas, altair" >nul 2>&1
if errorlevel 1 (
  echo Required packages are missing. Run the pip install command in README.md.
  pause
  exit /b 1
)
set "P717_DEMO_ARTIFACT="
".venv\Scripts\python.exe" -m streamlit run app.py --server.address=127.0.0.1
if errorlevel 1 (
  echo The app could not start. Check the message above and README.md.
  pause
  exit /b 1
)
endlocal
