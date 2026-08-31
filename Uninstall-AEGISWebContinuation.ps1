param([switch]$Apply)

$ErrorActionPreference = "Stop"
$pluginName = "aegis-web-continuation"
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourcePlugin = Join-Path $packageRoot "plugins\$pluginName"
$destinationPlugin = Join-Path (Join-Path $HOME "plugins") $pluginName
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
    throw "PACKAGE_INCOMPLETE: plugin source is required for safe fingerprint comparison"
}
Assert-NoReparsePoint $sourcePlugin
$destinationExists = Test-Path -LiteralPath $destinationPlugin -PathType Container
if ($destinationExists) {
    Assert-NoReparsePoint $destinationPlugin
    if ((Get-TreeFingerprint $destinationPlugin) -ne (Get-TreeFingerprint $sourcePlugin)) {
        throw "PLUGIN_MODIFIED: installed plugin differs from this package; uninstall stopped"
    }
}
elseif (Test-Path -LiteralPath $destinationPlugin) {
    throw "PLUGIN_CONFLICT: destination is not a directory"
}

$marketplaceExists = Test-Path -LiteralPath $marketplacePath -PathType Leaf
$entryExists = $false
if ($marketplaceExists) {
    try { $marketplace = Get-Content -Raw -LiteralPath $marketplacePath | ConvertFrom-Json }
    catch { throw "MARKETPLACE_CONFLICT: existing marketplace.json is invalid JSON" }
    $matchingEntries = @($marketplace.plugins | Where-Object { $_.name -eq $pluginName })
    if ($matchingEntries.Count -gt 1) { throw "MARKETPLACE_CONFLICT: duplicate plugin entries" }
    $entryExists = $matchingEntries.Count -eq 1
    if ($entryExists -and ($matchingEntries[0].source.source -ne "local" -or $matchingEntries[0].source.path -ne $expectedSource)) {
        throw "MARKETPLACE_CONFLICT: plugin entry points elsewhere"
    }
}

Write-Host "[AEGIS] Plugin destination: $destinationPlugin"
Write-Host "[AEGIS] Marketplace entry present: $entryExists"
if (-not $Apply) {
    Write-Host "[AEGIS] PREVIEW_ONLY: no files were changed. Run again with -Apply."
    return
}

$marketplaceBackup = $null
$marketplaceTemp = "$marketplacePath.tmp-$([guid]::NewGuid().ToString('N'))"
$quarantine = "$destinationPlugin.remove-$([guid]::NewGuid().ToString('N'))"
try {
    if ($destinationExists) {
        Move-Item -LiteralPath $destinationPlugin -Destination $quarantine
    }
    if ($entryExists) {
        $marketplace.plugins = @($marketplace.plugins | Where-Object { $_.name -ne $pluginName })
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $marketplaceBackup = "$marketplacePath.aegis-backup-$stamp"
        Copy-Item -LiteralPath $marketplacePath -Destination $marketplaceBackup
        $marketplaceJson = $marketplace | ConvertTo-Json -Depth 20
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [IO.File]::WriteAllText($marketplaceTemp, $marketplaceJson, $utf8NoBom)
        Move-Item -LiteralPath $marketplaceTemp -Destination $marketplacePath -Force
    }
    if (Test-Path -LiteralPath $quarantine -PathType Container) {
        Remove-Item -LiteralPath $quarantine -Recurse -Force
    }
}
catch {
    Remove-Item -LiteralPath $marketplaceTemp -Force -ErrorAction SilentlyContinue
    if ($marketplaceBackup -and (Test-Path -LiteralPath $marketplaceBackup -PathType Leaf)) {
        Copy-Item -LiteralPath $marketplaceBackup -Destination $marketplacePath -Force
    }
    if ((Test-Path -LiteralPath $quarantine -PathType Container) -and -not (Test-Path -LiteralPath $destinationPlugin)) {
        Move-Item -LiteralPath $quarantine -Destination $destinationPlugin
    }
    throw
}

Write-Host "[AEGIS] Plugin source and its exact marketplace entry were removed. Restart ChatGPT to refresh plugin discovery."
