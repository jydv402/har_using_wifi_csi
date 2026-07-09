param (
    [switch]$up,
    [switch]$pack,
    [switch]$clean,
    [switch]$v2,
    [switch]$v3,
    [switch]$h
)

if ($h) {
    Write-Host "Usage: .\open_venv.ps1 [-up] [-pack] [-clean] [-v2] [-v3] [-h]"
    Write-Host "-up: Update pip"
    Write-Host "-pack: Install requirements"
    Write-Host "-clean: Clear screen"
    Write-Host "-v2: Change directory to project_v2"
    Write-Host "-v3: Change directory to project_v3"
    Write-Host "-h: Show this help message"
    return
}

# If venv is not present, create it
if (-not (Test-Path "venv")) {
    python -m venv venv
}

# Activate the venv
.\venv\Scripts\Activate.ps1

# Update pip if -up argument was provided
if ($up) {
    python.exe -m pip install --upgrade pip
}

# Clear
clear

# If the -pack argument was provided, install requirements
if ($pack) {
    if (Test-Path "requirements.txt") {
        Write-Host "Installing requirements..." -ForegroundColor Cyan
        pip install -r requirements.txt
    } else {
        Write-Warning "requirements.txt not found. Skipping installation."
    }
}

if ($clean) {
    clear
}

if ($v2) {
    cd .\project_v2\
}

if ($v3) {
    cd .\project_v3\
}