<#
.SYNOPSIS
    Universal One-Click Setup & Launch Script for Windows 10 and Windows 11.
.DESCRIPTION
    Automates prerequisite detection/installation (Python 3.12, Node.js via winget),
    virtual environment creation, dependency installation, storage setup,
    database seeding, and starts both Backend (FastAPI) and Frontend (Vite) servers.
.PARAMETER SetupOnly
    If specified, performs setup and exits without starting the development servers.
.PARAMETER ForceReinstall
    If specified, removes existing virtual environment and node_modules for a clean install.
.EXAMPLE
    .\setup-windows.ps1
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1
#>

[CmdletBinding()]
param(
    [switch]$SetupOnly,
    [switch]$ForceReinstall
)

$ErrorActionPreference = "Stop"

# Helper: Print styled headers and messages
function Write-Title ($text) {
    Write-Host "`n=================================================================" -ForegroundColor Cyan
    Write-Host "  $text" -ForegroundColor White
    Write-Host "=================================================================" -ForegroundColor Cyan
}

function Write-Step ($step, $text) {
    Write-Host "`n[$step] " -ForegroundColor Yellow -NoNewline
    Write-Host $text -ForegroundColor Green
}

function Write-Info ($text) {
    Write-Host "    $text" -ForegroundColor Gray
}

function Write-Success ($text) {
    Write-Host "    [OK] $text" -ForegroundColor Green
}

function Write-Warn ($text) {
    Write-Host "    [!] $text" -ForegroundColor Yellow
}

# Helper: Reload environment variables from registry into current process
function Update-SessionEnvironment {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

# Helper: Find Python executable
function Get-PythonExecutable {
    Update-SessionEnvironment
    $possiblePaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Program Files\Python312\python.exe",
        "C:\Program Files\Python311\python.exe",
        "C:\Program Files\Python310\python.exe"
    )

    foreach ($p in $possiblePaths) {
        if (Test-Path $p) { return $p }
    }

    # Search any Python 3.x in LocalAppData or Program Files
    $discovered = Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\Python", "C:\Program Files\Python*" -Filter "python.exe" -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName -First 1
    if ($discovered -and (Test-Path $discovered)) { return $discovered }

    # Check PATH command
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and ($cmd.Source -notlike "*WindowsApps*")) {
        return $cmd.Source
    }

    return $null
}

# Helper: Find npm executable (prefer npm.cmd to avoid PS execution policy restrictions)
function Get-NpmExecutable {
    Update-SessionEnvironment
    $possiblePaths = @(
        "C:\Program Files\nodejs\npm.cmd",
        "$env:LOCALAPPDATA\Programs\nodejs\npm.cmd",
        "$env:APPDATA\npm\npm.cmd"
    )

    foreach ($p in $possiblePaths) {
        if (Test-Path $p) { return $p }
    }

    $cmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $cmdNpm = Get-Command npm -ErrorAction SilentlyContinue
    if ($cmdNpm) { return $cmdNpm.Source }

    return $null
}

# -------------------------------------------------------------------------
# Start Setup
# -------------------------------------------------------------------------
Clear-Host
Write-Title "CredVerify Platform - Universal Windows Setup (Win 10/11)"
Write-Host "Target Environment: Windows 10 / Windows 11 (x64 / ARM64)" -ForegroundColor Cyan
Write-Host "Automated Installer & Environment Provisioner" -ForegroundColor Gray

# 1. Determine script directory
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (!(Test-Path "$ScriptRoot\backend") -and (Test-Path "$ScriptRoot\SSBT\backend")) {
    $ScriptRoot = "$ScriptRoot\SSBT"
}
$BackendDir = "$ScriptRoot\backend"
$FrontendDir = "$ScriptRoot\frontend"

Write-Info "Working Directory: $ScriptRoot"

# 2. Check / Install Python
Write-Step "1/5" "Checking Python Runtime..."
$pythonExe = Get-PythonExecutable

if (-not $pythonExe) {
    Write-Warn "Python runtime not detected. Attempting automated install via winget..."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            Write-Info "Running: winget install Python.Python.3.12..."
            winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
            Update-SessionEnvironment
            $pythonExe = Get-PythonExecutable
        } catch {
            Write-Warn "Winget installation encountered an issue: $_"
        }
    }
}

if (-not $pythonExe) {
    Write-Host "`n[ERROR] Python 3.12 could not be found or automatically installed." -ForegroundColor Red
    Write-Host "Please install Python 3.12 from https://www.python.org/downloads/ (check 'Add Python to PATH') and re-run this script." -ForegroundColor Yellow
    exit 1
}

$pyVer = & $pythonExe --version 2>&1
Write-Success "Python ready: $pythonExe ($pyVer)"

# 3. Check / Install Node.js
Write-Step "2/5" "Checking Node.js & npm..."
$npmExe = Get-NpmExecutable

if (-not $npmExe) {
    Write-Warn "Node.js / npm not detected. Attempting automated install via winget..."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            Write-Info "Running: winget install OpenJS.NodeJS.LTS..."
            winget install --id OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
            Update-SessionEnvironment
            $npmExe = Get-NpmExecutable
        } catch {
            Write-Warn "Winget installation encountered an issue: $_"
        }
    }
}

if (-not $npmExe) {
    Write-Host "`n[ERROR] Node.js could not be found or automatically installed." -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/ and re-run this script." -ForegroundColor Yellow
    exit 1
}

$nodeVer = & $npmExe --version 2>&1
Write-Success "Node.js package manager ready: $npmExe (v$nodeVer)"

# 4. Configure Backend Environment & Dependencies
Write-Step "3/5" "Configuring Backend (Python FastAPI)..."
Set-Location $BackendDir

$VenvDir = "$BackendDir\.venv"
if ($ForceReinstall -and (Test-Path $VenvDir)) {
    Write-Info "Removing existing virtual environment for clean reinstall..."
    Remove-Item -Recurse -Force $VenvDir -ErrorAction SilentlyContinue
}

if (!(Test-Path $VenvDir)) {
    Write-Info "Creating Python virtual environment in $VenvDir..."
    & $pythonExe -m venv $VenvDir
}

$VenvPython = "$VenvDir\Scripts\python.exe"
$VenvPip = "$VenvDir\Scripts\pip.exe"

if (!(Test-Path $VenvPython)) {
    Write-Host "`n[ERROR] Failed to locate virtual environment python at $VenvPython" -ForegroundColor Red
    exit 1
}

Write-Info "Upgrading pip and installing backend dependencies..."
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPip install -r requirements.txt --quiet
Write-Success "Backend dependencies installed successfully."

# Create required storage directories
$dirs = @("storage/certificates", "storage/qr", "storage/uploads", "storage/temp", "data")
foreach ($dir in $dirs) {
    $fullDirPath = "$BackendDir\$dir"
    if (!(Test-Path $fullDirPath)) {
        New-Item -ItemType Directory -Force -Path $fullDirPath | Out-Null
    }
}
Write-Success "Storage and database directories initialized."

# Create .env from .env.example if missing
if (!(Test-Path "$BackendDir\.env")) {
    if (Test-Path "$BackendDir\.env.example") {
        Copy-Item "$BackendDir\.env.example" "$BackendDir\.env"
        Write-Success "Created .env configuration file."
    }
}

# Seed database
Write-Info "Seeding database with demo records..."
& $VenvPython -m app.seed
Write-Success "Database seeded with demo users and institutions."

# 5. Configure Frontend Environment & Dependencies
Write-Step "4/5" "Configuring Frontend (React + Vite)..."
Set-Location $FrontendDir

if ($ForceReinstall -and (Test-Path "$FrontendDir\node_modules")) {
    Write-Info "Removing existing node_modules for clean reinstall..."
    Remove-Item -Recurse -Force "$FrontendDir\node_modules" -ErrorAction SilentlyContinue
}

if (!(Test-Path "$FrontendDir\node_modules")) {
    Write-Info "Installing frontend packages with npm..."
    & $npmExe install
    Write-Success "Frontend packages installed."
} else {
    Write-Success "Frontend node_modules already present."
}

# 6. Launch or Exit
Write-Step "5/5" "Setup Verification Complete!"

if ($SetupOnly) {
    Write-Title "Setup Completed Successfully!"
    Write-Host "You can launch the platform anytime with: .\setup-windows.ps1" -ForegroundColor Cyan
    exit 0
}

Write-Title "Launching CredVerify Platform"
Write-Host "Starting Backend server on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Set-Location $BackendDir
Start-Process -NoNewWindow -FilePath (Resolve-Path $VenvPython) -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000"

Start-Sleep -Seconds 2

Write-Host "Starting Frontend server on http://127.0.0.1:5173 ..." -ForegroundColor Cyan
Set-Location $FrontendDir

# Open default browser after brief delay
Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-NoProfile -Command `"Start-Sleep -Seconds 3; Start-Process 'http://localhost:5173'`""

Write-Host "`n-----------------------------------------------------------------" -ForegroundColor Green
Write-Host "  Platform Services are Running:" -ForegroundColor Green
Write-Host "  * Frontend UI:   http://localhost:5173" -ForegroundColor White
Write-Host "  * Backend API:   http://localhost:8000" -ForegroundColor White
Write-Host "  * Swagger Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "`n  Demo Credentials:" -ForegroundColor Green
Write-Host "  * Super Admin:   admin@credverify.demo / admin123" -ForegroundColor White
Write-Host "  * Inst Admin:    instadmin@demo-institute.edu / instadmin123" -ForegroundColor White
Write-Host "-----------------------------------------------------------------`n" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the frontend server." -ForegroundColor Gray

& $npmExe run dev -- --host 127.0.0.1 --port 5173
