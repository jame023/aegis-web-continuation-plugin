param([switch]$Apply)

$ErrorActionPreference = "Stop"
$pluginName = "aegis-web-continuation"
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourcePlugin = Join-Path $packageRoot "plugins\$pluginName"
$destinationParent = Join-Path $HOME "plugins"
$destinationPlugin = Join-Path $destinationParent $pluginName
$marketplacePath = Join-Path $HOME ".agents\plugins\marketplace.json"
$expectedSource = "./plugins/$pluginName"

function Assert-NoReparsePoint([string]$Root) {
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return }
    foreach ($item in Get-ChildItem -Force -Recurse -LiteralPath $Root) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "PLUGIN_BOUNDARY: reparse point/symlink is not allowed: $($item.FullName)"
        }
    }
}

function Get-TreeFingerprint([string]$Root) {
    $rootPath = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $rows = @()
    foreach ($item in Get-ChildItem -Force -Recurse -File -LiteralPath $rootPath | Sort-Object FullName) {
        $relative = $item.FullName.Substring($rootPath.Length).TrimStart('\', '/').Replace('\', '/')
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $item.FullName).Hash.ToLowerInvariant()
        $rows += "$relative`t$hash"
    }
    $bytes = [Text.Encoding]::UTF8.GetBytes(($rows -join "`n"))
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "").ToLowerInvariant() }
    finally { $sha.Dispose() }
}

if (-not (Test-Path -LiteralPath $sourcePlugin -PathType Container)) {
    throw "PACKAGE_INCOMPLETE: missing plugin source $sourcePlugin"
}
Assert-NoReparsePoint $sourcePlugin
$manifestPath = Join-Path $sourcePlugin ".codex-plugin\plugin.json"
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "PACKAGE_INCOMPLETE: missing plugin.json"
}
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
if ($manifest.name -ne $pluginName -or $manifest.version -ne "1.0.0") {
    throw "PACKAGE_INCOMPLETE: unexpected plugin identity/version"
}

$sourceFingerprint = Get-TreeFingerprint $sourcePlugin
$destinationExists = Test-Path -LiteralPath $destinationPlugin -PathType Container
if ($destinationExists) {
    Assert-NoReparsePoint $destinationPlugin
    if ((Get-TreeFingerprint $destinationPlugin) -ne $sourceFingerprint) {
        throw "PLUGIN_CONFLICT: destination exists with different content: $destinationPlugin"
    }
}
elseif (Test-Path -LiteralPath $destinationPlugin) {
    throw "PLUGIN_CONFLICT: destination exists and is not a directory: $destinationPlugin"
}

$marketplaceExists = Test-Path -LiteralPath $marketplacePath -PathType Leaf
if ($marketplaceExists) {
    try { $marketplace = Get-Content -Raw -LiteralPath $marketplacePath | ConvertFrom-Json }
    catch { throw "MARKETPLACE_CONFLICT: existing marketplace.json is invalid JSON" }
    if (-not $marketplace.name) { throw "MARKETPLACE_CONFLICT: marketplace name is missing" }
    if ($null -eq $marketplace.plugins) {
        $marketplace | Add-Member -NotePropertyName plugins -NotePropertyValue @()
    }
}
elseif (Test-Path -LiteralPath $marketplacePath) {
    throw "MARKETPLACE_CONFLICT: marketplace path exists and is not a file"
}
else {
    $marketplace = [pscustomobject][ordered]@{
        name = "personal"
        interface = [pscustomobject][ordered]@{ displayName = "Personal" }
        plugins = @()
    }
}

$matchingEntries = @($marketplace.plugins | Where-Object { $_.name -eq $pluginName })
if ($matchingEntries.Count -gt 1) {
    throw "MARKETPLACE_CONFLICT: duplicate plugin entries"
}
$entryExists = $matchingEntries.Count -eq 1
if ($entryExists) {
    $entry = $matchingEntries[0]
    if ($entry.source.source -ne "local" -or $entry.source.path -ne $expectedSource) {
        throw "MARKETPLACE_CONFLICT: existing plugin entry points elsewhere"
    }
}

Write-Host "[AEGIS] Plugin source fingerprint: $sourceFingerprint"
Write-Host "[AEGIS] Plugin destination: $destinationPlugin"
Write-Host "[AEGIS] Marketplace: $marketplacePath"
if (-not $Apply) {
    Write-Host "[AEGIS] PREVIEW_ONLY: no files were changed. Run again with -Apply."
    return
}

$createdPlugin = $false
$createdMarketplace = -not $marketplaceExists
$marketplaceBackup = $null
$marketplaceTemp = "$marketplacePath.tmp-$([guid]::NewGuid().ToString('N'))"
try {
    if (-not $destinationExists) {
        New-Item -ItemType Directory -Force -Path $destinationParent | Out-Null
        Copy-Item -LiteralPath $sourcePlugin -Destination $destinationPlugin -Recurse
        $createdPlugin = $true
    }

    if (-not $entryExists) {
        $newEntry = [pscustomobject][ordered]@{
            name = $pluginName
            source = [pscustomobject][ordered]@{ source = "local"; path = $expectedSource }
            policy = [pscustomobject][ordered]@{ installation = "AVAILABLE"; authentication = "ON_INSTALL" }
            category = "Productivity"
        }
        $marketplace.plugins = @($marketplace.plugins) + @($newEntry)
        $marketplaceDirectory = Split-Path -Parent $marketplacePath
        New-Item -ItemType Directory -Force -Path $marketplaceDirectory | Out-Null
        if ($marketplaceExists) {
            $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
            $marketplaceBackup = "$marketplacePath.aegis-backup-$stamp"
            Copy-Item -LiteralPath $marketplacePath -Destination $marketplaceBackup
        }
        $marketplaceJson = $marketplace | ConvertTo-Json -Depth 20
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [IO.File]::WriteAllText($marketplaceTemp, $marketplaceJson, $utf8NoBom)
        Move-Item -LiteralPath $marketplaceTemp -Destination $marketplacePath -Force
    }
}
catch {
    Remove-Item -LiteralPath $marketplaceTemp -Force -ErrorAction SilentlyContinue
    if ($marketplaceBackup -and (Test-Path -LiteralPath $marketplaceBackup -PathType Leaf)) {
        Copy-Item -LiteralPath $marketplaceBackup -Destination $marketplacePath -Force
    }
    elseif ($createdMarketplace -and (Test-Path -LiteralPath $marketplacePath -PathType Leaf)) {
        Remove-Item -LiteralPath $marketplacePath -Force
    }
    if ($createdPlugin -and (Test-Path -LiteralPath $destinationPlugin -PathType Container)) {
        Remove-Item -LiteralPath $destinationPlugin -Recurse -Force
    }
    throw
}

Write-Host "[AEGIS] Plugin source installed. Restart ChatGPT desktop, install it from Plugins > Personal, then start a new Web chat."
Write-Host "[AEGIS] No GitHub connection, credential, repository permission, merge, or deployment setting was changed."
