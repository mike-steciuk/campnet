$ErrorActionPreference = "Stop"

# Always run from the project root so the environment and surveys are found.
Set-Location -LiteralPath $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "CampNet environment not found. Create .venv and install the project first."
}

# Open the interactive location, site, and scan-date browser.
& $python -m campnet review
