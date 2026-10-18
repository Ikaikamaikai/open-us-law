# Downloads every decision PDF listed on the Hawaii DCCA Office of Administrative Hearings search page:
#   https://web3.dcca.hawaii.gov/oah/public/result?search=&cat=All
# Saves each PDF under the state's own file name, plus a manifest with each file's size, SHA-256 fingerprint,
# source address and download date, and a copy of the search page as it looked that day.
# Safe to stop (Ctrl+C) and run again: files already downloaded are skipped.
# Run in PowerShell:  powershell -ExecutionPolicy Bypass -File "<path to this file>"
param(
    [string]$Destination = (Join-Path $HOME 'hi-dcca-oah-pdfs_2026-10-18'),
    [int]$Limit = 0
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$base = 'https://web3.dcca.hawaii.gov'
$listUrl = "$base/oah/public/result?search=&cat=All"
$today = Get-Date -Format 'yyyy-MM-dd'

New-Item -ItemType Directory -Force -Path $Destination | Out-Null
$Destination = (Resolve-Path -LiteralPath $Destination).ProviderPath
$freeGB = [math]::Round((Get-PSDrive -Name (Get-Item -LiteralPath $Destination).PSDrive.Name).Free / 1GB, 1)
Write-Host "Saving to: $Destination  (free space: $freeGB GB)"
if ($Limit -eq 0 -and $freeGB -lt 20) {
    Read-Host "The full download needs about 16 GB. Press Enter to continue anyway, or close this window to stop"
}

$snapshot = Join-Path $Destination "hi-dcca-oah-search-page-snapshot_$today.html"
Invoke-WebRequest -Uri $listUrl -OutFile $snapshot -UseBasicParsing -TimeoutSec 300
$html = [IO.File]::ReadAllText($snapshot)
$names = @([regex]::Matches($html, 'href="/oah/public/docs/([^"]+)"') |
    ForEach-Object { [Net.WebUtility]::HtmlDecode($_.Groups[1].Value) } |
    Sort-Object -Unique)
Write-Host "PDFs listed on the state's page today: $($names.Count)"
if ($names.Count -lt 1000) { throw "Found only $($names.Count) PDF links; the state's page may have changed. Nothing was downloaded." }

$manifest = Join-Path $Destination 'hi-dcca-oah-pdf-manifest.csv'
$done = @{}
if (Test-Path -LiteralPath $manifest) {
    Import-Csv -LiteralPath $manifest | ForEach-Object { $done[$_.pdf_filename] = $true }
} else {
    Set-Content -LiteralPath $manifest -Value 'pdf_filename,size_bytes,sha256,source_url,retrieved_on' -Encoding ASCII
}

$temp = Join-Path $Destination 'download-in-progress.part'
$ok = 0; $skipped = 0; $failed = New-Object System.Collections.Generic.List[string]; $n = 0
foreach ($name in $names) {
    $n++
    if ($Limit -gt 0 -and ($ok + $failed.Count) -ge $Limit) { break }
    $target = Join-Path $Destination $name
    if ($done.ContainsKey($name) -and (Test-Path -LiteralPath $target)) { $skipped++; continue }
    if ($target.Length -gt 259) { $failed.Add("$name  (folder path too long for Windows)"); continue }
    $url = "$base/oah/public/docs/" + [uri]::EscapeDataString($name)
    $saved = $false; $reason = ''
    for ($try = 1; $try -le 3 -and -not $saved; $try++) {
        $reason = ''
        try {
            $resp = Invoke-WebRequest -Uri $url -OutFile $temp -UseBasicParsing -TimeoutSec 600 -PassThru
            $expected = $resp.Headers['Content-Length']; if ($expected -is [array]) { $expected = $expected[0] }
            $got = (Get-Item -LiteralPath $temp).Length
            if ($expected -and ([int64]$expected -ne $got)) { $reason = "incomplete download ($got of $expected bytes)"; throw $reason }
            $fs = [IO.File]::OpenRead($temp); $head = New-Object byte[] 4; [void]$fs.Read($head, 0, 4); $fs.Close()
            if ([Text.Encoding]::ASCII.GetString($head) -ne '%PDF') { $reason = 'not a PDF'; throw $reason }
            Move-Item -LiteralPath $temp -Destination $target -Force
            $saved = $true
        } catch {
            if (-not $reason) { $reason = $_.Exception.Message }
            Start-Sleep -Seconds (5 * $try)
        }
    }
    if ($saved) {
        $size = (Get-Item -LiteralPath $target).Length
        $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLower()
        Add-Content -LiteralPath $manifest -Value ('"{0}",{1},{2},"{3}",{4}' -f $name, $size, $hash, $url, (Get-Date -Format 'yyyy-MM-dd')) -Encoding ASCII
        $ok++
        Write-Host ("[{0}/{1}] {2}" -f $n, $names.Count, $name)
    } else {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force }
        $failed.Add("$name  ($reason)")
        Write-Host ("[{0}/{1}] FAILED {2}" -f $n, $names.Count, $name)
    }
    Start-Sleep -Milliseconds 500
}

if ($failed.Count -gt 0) {
    $problems = Join-Path $Destination "hi-dcca-oah-pdf-download-problems_$today.txt"
    Set-Content -LiteralPath $problems -Value $failed -Encoding ASCII
}
$present = @($names | Where-Object { Test-Path -LiteralPath (Join-Path $Destination $_) }).Count
Write-Host ""
Write-Host "Downloaded now: $ok   Already had: $skipped   Failed: $($failed.Count)"
Write-Host "In the folder: $present of the $($names.Count) PDFs listed on the state's page today"
if ($failed.Count -gt 0) { Write-Host "Failed files are listed in $problems. Run this script again to retry them." }
Write-Host "Folder: $Destination"
