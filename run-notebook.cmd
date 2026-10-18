@echo off
setlocal
pushd "%~dp0" || exit /b 1
if not exist ".venv\Scripts\jupyter-lab.exe" (
    echo Notebook support is missing. Run setup-windows.cmd first.
    popd
    exit /b 1
)
set "PYTHONUTF8=1"
set "OMP_NUM_THREADS=1"
set "OPENBLAS_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
set "NUMEXPR_NUM_THREADS=1"
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
set "notebook=notebooks\Cyber_Threat_MultiAgent.ipynb"
if exist "notebooks\Cyber_Threat_MultiAgent.v2.ipynb" set "notebook=notebooks\Cyber_Threat_MultiAgent.v2.ipynb"
if exist "notebooks\Cyber_Threat_MultiAgent.v2.executed.ipynb" set "notebook=notebooks\Cyber_Threat_MultiAgent.v2.executed.ipynb"
if exist "notebooks\Cyber_Threat_MultiAgent.v2.evaluation.ipynb" set "notebook=notebooks\Cyber_Threat_MultiAgent.v2.evaluation.ipynb"
if exist "notebooks\Cyber_Threat_MultiAgent.v2.evaluation.executed.ipynb" set "notebook=notebooks\Cyber_Threat_MultiAgent.v2.evaluation.executed.ipynb"
".venv\Scripts\python.exe" -m jupyterlab --ServerApp.root_dir="%CD%" "%notebook%" %*
set "result=%errorlevel%"
popd
exit /b %result%
