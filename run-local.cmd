@echo off
setlocal
pushd "%~dp0" || exit /b 1
if not exist ".venv\Scripts\python.exe" (
    echo Project environment is missing. Run setup-windows.cmd first.
    popd
    exit /b 1
)
set "PYTHONUTF8=1"
set "OMP_NUM_THREADS=1"
set "OPENBLAS_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
set "NUMEXPR_NUM_THREADS=1"
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
if "%~1"=="" goto live
if /I "%~1"=="test" goto tests
".venv\Scripts\python.exe" -m cyberagents %*
goto done
:tests
".venv\Scripts\python.exe" -m pytest -m "not live"
goto done
:live
".venv\Scripts\python.exe" -m cyberagents run --system S3 --seed 42 --live
:done
set "result=%errorlevel%"
popd
if "%~1"=="" pause
exit /b %result%
