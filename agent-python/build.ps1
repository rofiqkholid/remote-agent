# Build MSI installer using WiX Toolset
# Prerequisites: Install WiX Toolset from https://wixtoolset.org/

Write-Host "Building MSI installer..." -ForegroundColor Green

# Check if WiX is installed
$wixPath = "C:\Program Files (x86)\WiX Toolset v3.11\bin"
if (-not (Test-Path $wixPath)) {
    Write-Host "`nWiX Toolset not found!" -ForegroundColor Red
    Write-Host "Please install WiX Toolset from: https://github.com/wixtoolset/wix3/releases" -ForegroundColor Yellow
    Write-Host "Download: wix311.exe" -ForegroundColor Cyan
    exit 1
}

$env:PATH += ";$wixPath"

# Compile WiX source
Write-Host "Compiling WiX source..." -ForegroundColor Cyan
& candle.exe agent.wxs

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nCompilation failed!" -ForegroundColor Red
    exit 1
}

# Link to create MSI
Write-Host "Creating MSI package..." -ForegroundColor Cyan
& light.exe -ext WixUIExtension agent.wixobj -out AgentMonitoring.msi

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nMSI created successfully!" -ForegroundColor Green
    Write-Host "Location: AgentMonitoring.msi" -ForegroundColor Cyan
} else {
    Write-Host "`nMSI creation failed!" -ForegroundColor Red
}
