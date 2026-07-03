
$ErrorActionPreference = "Stop"

$REPO_URL    = "https://github.com/IdanTheMan/hertz-forge/archive/refs/heads/main.zip"
$INSTALL_DIR = Join-Path $env:APPDATA "HertzForge"
$ZIP_PATH    = Join-Path $env:TEMP "hertz-forge.zip"

# ── banner ──
Write-Host ""
Write-Host "  ██╗  ██╗███████╗██████╗ ████████╗███████╗" -ForegroundColor Cyan
Write-Host "  ██║  ██║██╔════╝██╔══██╗╚══██╔══╝╚════██║ " -ForegroundColor Cyan
Write-Host "  ███████║█████╗  ██████╔╝   ██║      ██╔═╝  " -ForegroundColor Cyan
Write-Host "  ██╔══██║██╔══╝  ██╔══██╗   ██║    ██╔═╝   " -ForegroundColor Cyan
Write-Host "  ██║  ██║███████╗██║  ██║   ██║   ███████║" -ForegroundColor Cyan
Write-Host "  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝" -ForegroundColor Cyan
Write-Host "  Hertz Forge — Brainwave Entrainment Generator" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow

$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3") {
            $pythonCmd = $cmd
            Write-Host "  Found: $ver" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "  Python 3 not found. Installing via winget..." -ForegroundColor Yellow
    try {
        winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $pythonCmd = "python"
        Write-Host "  Python installed." -ForegroundColor Green
    } catch {
        Write-Host "  ERROR: Could not install Python automatically." -ForegroundColor Red
        Write-Host "  Please install Python 3.9+ from https://python.org and re-run." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "[2/5] Downloading Hertz Forge..." -ForegroundColor Yellow

try {
    Invoke-WebRequest -Uri $REPO_URL -OutFile $ZIP_PATH -UseBasicParsing
    Write-Host "  Downloaded." -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Could not download from GitHub." -ForegroundColor Red
    Write-Host "  Check your internet connection." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[3/5] Extracting to $INSTALL_DIR ..." -ForegroundColor Yellow

if (Test-Path $INSTALL_DIR) {
    Remove-Item -Recurse -Force $INSTALL_DIR
}

try {
    Expand-Archive -Path $ZIP_PATH -DestinationPath $env:TEMP -Force
    $extracted = Join-Path $env:TEMP "hertz-forge-main"
    Move-Item -Path $extracted -Destination $INSTALL_DIR
    Remove-Item -Force $ZIP_PATH -ErrorAction SilentlyContinue
    Write-Host "  Extracted." -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Could not extract files." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[4/5] Installing dependencies..." -ForegroundColor Yellow

try {
    & $pythonCmd -m pip install --quiet --user -r "$INSTALL_DIR\requirements.txt" 2>&1 | Out-Null
    Write-Host "  Dependencies installed." -ForegroundColor Green
} catch {
    Write-Host "  WARNING: pip install had issues. Trying anyway..." -ForegroundColor Yellow
}

Write-Host "[5/5] Creating desktop shortcuts..." -ForegroundColor Yellow

$desktopPath = [Environment]::GetFolderPath("Desktop")
$pythonPath = (Get-Command $pythonCmd -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) { $pythonPath = $pythonCmd }

try {
    $ws = New-Object -ComObject WScript.Shell

    $shortcut1 = $ws.CreateShortcut((Join-Path $desktopPath "Hertz Forge.lnk"))
    $shortcut1.TargetPath = $pythonPath
    $shortcut1.Arguments = "`"$INSTALL_DIR\run.py`""
    $shortcut1.WorkingDirectory = $INSTALL_DIR
    $shortcut1.Description = "Hertz Forge - Brainwave Entrainment"
    $shortcut1.Save()
    Write-Host "  Created shortcut: Hertz Forge" -ForegroundColor Green

    $shortcut2 = $ws.CreateShortcut((Join-Path $desktopPath "Hertz Forge Playlist.lnk"))
    $shortcut2.TargetPath = $pythonPath
    $shortcut2.Arguments = "`"$INSTALL_DIR\run_playlist.py`""
    $shortcut2.WorkingDirectory = $INSTALL_DIR
    $shortcut2.Description = "Hertz Forge - Playlist Mode"
    $shortcut2.Save()
    Write-Host "  Created shortcut: Hertz Forge Playlist" -ForegroundColor Green
} catch {
    Write-Host "  Could not create shortcuts (not critical)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Hertz Forge installed to: $INSTALL_DIR" -ForegroundColor Cyan
Write-Host "  Launching..." -ForegroundColor Cyan
Write-Host ""

Start-Process -FilePath $pythonPath -ArgumentList "`"$INSTALL_DIR\run.py`"" -WorkingDirectory $INSTALL_DIR