# PowerShell script to install Google Chrome and matching ChromeDriver on Windows
# Save this file as install_chrome_windows.ps1 and run it via install_chrome_windows.bat

function Install-Chrome {
    Write-Host "Checking for existing Google Chrome..."
    $chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
    if (-Not (Test-Path $chromePath)) {
        $chromePath = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    }
    if (Test-Path $chromePath) {
        Write-Host "Google Chrome already installed at $chromePath"
        return $chromePath
    }
    Write-Host "Google Chrome not found. Downloading installer..."
    $installerUrl = "https://dl.google.com/chrome/install/GoogleChromeStandaloneEnterprise64.msi"
    $tempInstaller = "$env:TEMP\ChromeInstaller.msi"
    Invoke-WebRequest -Uri $installerUrl -OutFile $tempInstaller -UseBasicParsing
    Write-Host "Running Chrome installer..."
    Start-Process msiexec.exe -ArgumentList "/i `"$tempInstaller`" /quiet /norestart" -Wait -NoNewWindow
    Remove-Item $tempInstaller -Force
    if (Test-Path $chromePath) {
        Write-Host "Google Chrome installed successfully."
        return $chromePath
    } else {
        Write-Error "Failed to install Google Chrome."
        exit 1
    }
}

function Get-ChromeVersion {
    param([string]$chromeExe)
    $fileInfo = Get-Item $chromeExe
    $versionInfo = $fileInfo.VersionInfo
    return $versionInfo.ProductVersion
}

function Install-ChromeDriver {
    param([string]$chromeVersion)
    # Extract major version (e.g., 124 from 124.0.6367.91)
    $majorVersion = $chromeVersion.Split('.')[0]
    Write-Host "Chrome major version: $majorVersion"
    $driverUrl = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$majorVersion"
    Write-Host "Fetching latest ChromeDriver for version $majorVersion..."
    $latestRelease = Invoke-WebRequest -Uri $driverUrl -UseBasicParsing
    $driverVersion = $latestRelease.Content.Trim()
    Write-Host "Latest ChromeDriver version: $driverVersion"
    $zipUrl = "https://chromedriver.storage.googleapis.com/$driverVersion/chromedriver_win32.zip"
    $zipPath = "$env:TEMP\chromedriver.zip"
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
    $extractPath = "C:\chromedriver"
    if (-Not (Test-Path $extractPath)) { New-Item -ItemType Directory -Path $extractPath | Out-Null }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $extractPath, $true)
    Remove-Item $zipPath -Force
    Write-Host "ChromeDriver extracted to $extractPath"
    # Add to PATH for the current session
    $env:Path = "$extractPath;$env:Path"
    Write-Host "ChromeDriver path added to session PATH."
}

# Main execution
$chromeExe = Install-Chrome
$chromeVer = Get-ChromeVersion -chromeExe $chromeExe
Write-Host "Detected Chrome version: $chromeVer"
Install-ChromeDriver -chromeVersion $chromeVer

Write-Host "Installation complete. You can now run the ClicToriano scripts."
