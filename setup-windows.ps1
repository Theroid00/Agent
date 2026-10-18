# Run from any directory with: powershell -NoProfile -ExecutionPolicy Bypass -File .\setup-windows.ps1
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONUTF8 = '1'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        throw 'Install 64-bit Python 3.12 with the Python launcher, then rerun setup-windows.cmd.'
    }
    & py -3.12 -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python 3.12 virtual environment.' }
}

& $python -c "import sys; print(sys.version); assert (3, 11) <= sys.version_info[:2] <= (3, 13), 'Python 3.11-3.13 required'; assert sys.maxsize > 2**32, '64-bit Python required'"
if ($LASTEXITCODE -ne 0) { throw 'The project virtual environment is not usable. Check your Python installation.' }

& $python -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt') -r (Join-Path $PSScriptRoot 'requirements-notebook.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Resolve the reported error and rerun setup.' }
& $python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Installed dependencies are incompatible; see pip check output above.' }
& $python -m ipykernel install --sys-prefix --name python3 --display-name 'Python (.venv)'
if ($LASTEXITCODE -ne 0) { throw 'Could not register the project notebook kernel.' }

$envFile = Join-Path $PSScriptRoot '.env'
if (-not (Test-Path -LiteralPath $envFile)) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '.env.example') -Destination $envFile
}

& (Join-Path $PSScriptRoot 'run-local.cmd') --help
if ($LASTEXITCODE -ne 0) { throw 'CLI startup check failed.' }
Write-Host 'Setup complete. Offline checks: run-local.cmd test'
Write-Host 'Open the notebook: run-notebook.cmd'
Write-Host 'Download the knowledge base and embedding model: run-local.cmd prepare'
Write-Host 'For live development, enter GEMINI_API_KEY privately in .env, then double-click run-notebook.cmd.'
