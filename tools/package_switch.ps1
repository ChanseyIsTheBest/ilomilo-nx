# ilomilo-nx: the Switch package (the request's step 8), as banjo-nx's builds/ folders (katamari-nx's script, for
# ilomilo: its names, no four-core forwarder NPDM: katamari-nx's was made for its own program id):
#   builds/<date>_<time>_<name>/
#     COPY_TO_SD_switch_ilomilo-nx/    ilomilo-nx.nro, ilomilo.toml (the player's settings: app/ilomilo_switch.toml,
#                                      the fixed settings being compiled in) or renut.toml (dist's renut.toml) in a
#                                      KATAMARI_BUILTIN_CONFIG=OFF build (the option keeps katamari-nx's name),
#                                      configs/ (renut.toml, renut_play.toml, renut_ab.toml and the rest),
#                                      deko3d_shaders.bin (the prebuilt DKSH cache), game_root/ (your game files),
#                                      dlc/ (your DLC packages)
#     ilomilo-nx.elf                   the unstripped ELF of this NRO (profiles map to it)
#     source_<commit>.tgz              the source snapshot (git archive of the commit; no game data, no generated code)
#     README.txt, PACKAGE_NOTES.txt
# Nothing of the game's data goes in by default (the NRO holds the recompiled code; the DKSH cache is compiled shader
# code). -GameRoot copies an extracted game into game_root and -Dlc the DLC packages into dlc (installed at the first
# start), for the user's own SD card only: never into git, never uploaded.
#   powershell -File tools/package_switch.ps1 -Name rc1 [-Build app\out\switch] [-Notes <file>]
#       [-GameRoot D:\ilomilo\game] [-Dlc <folder of DLC packages>]
param([string]$Name = "package", [string]$Build = "app\out\switch", [string]$Notes = "", [string]$GameRoot = "",
      [string]$Dlc = "")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$free = (Get-PSDrive D).Free / 1GB
if ($free -lt 2) { throw ("D: has {0:N1} GB free: not packaging (the request: stop and say so)" -f $free) }
$b = Join-Path $root $Build
$nro = Join-Path $b "renut.nro"
$elf = Join-Path $b "renut"
if (-not (Test-Path $nro)) { throw "no NRO at $nro" }
$stamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$out = Join-Path (Split-Path -Parent $root) "builds\${stamp}_$Name"
$sd = Join-Path $out "COPY_TO_SD_switch_ilomilo-nx"
New-Item -ItemType Directory -Force $sd, (Join-Path $sd "configs"), (Join-Path $sd "game_root") | Out-Null
Copy-Item $nro (Join-Path $sd "ilomilo-nx.nro")
$dist = Join-Path $root "dist\switch\ilomilo-nx"
# The one toml the NRO reads (src/renut_app.h, OnConfigurePaths): in the built-in config's build the player's
# ilomilo.toml (its settings over the compiled-in ones); otherwise the full renut.toml.
$builtin = Select-String -Path (Join-Path $b "CMakeCache.txt") -Pattern "^KATAMARI_BUILTIN_CONFIG:BOOL=ON" -Quiet
if ($builtin) {
    Copy-Item (Join-Path $root "app\ilomilo_switch.toml") (Join-Path $sd "ilomilo.toml")
} else {
    Copy-Item (Join-Path $dist "renut.toml") (Join-Path $sd "renut.toml")
}
Copy-Item (Join-Path $dist "renut.toml"), (Join-Path $dist "renut_play.toml"), (Join-Path $dist "renut_ab.toml") (Join-Path $sd "configs")
Copy-Item (Join-Path $dist "configs\*.toml") (Join-Path $sd "configs")
$cache = Join-Path $root "out\deko3d_shaders\deko3d_shaders.bin"
if (Test-Path $cache) { Copy-Item $cache $sd }
if ($GameRoot) {
    $need = ((Get-ChildItem $GameRoot -Recurse -File | Measure-Object -Sum Length).Sum + 1GB) / 1GB
    if ((Get-PSDrive D).Free / 1GB -lt $need) { throw ("D: has too little space for the game files ({0:N1} GB needed)" -f $need) }
    & robocopy $GameRoot (Join-Path $sd "game_root") /E /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy of the game files failed ($LASTEXITCODE)" }
} else {
    Set-Content -Path (Join-Path $sd "game_root\PUT_YOUR_GAME_FILES_HERE.txt") -Encoding ascii -Value `
        "Extract your own ilomilo (XBLA) here: default.xex, Data/ and the rest, plus Title Update #1's default.xexp next to default.xex (README.txt)."
}
New-Item -ItemType Directory -Force (Join-Path $sd "dlc") | Out-Null
if ($Dlc) {
    Copy-Item (Join-Path $Dlc "*") (Join-Path $sd "dlc") -Force
} else {
    Set-Content -Path (Join-Path $sd "dlc\PUT_THE_DLC_PACKAGES_HERE.txt") -Encoding ascii -Value `
        "Optional: ilomilo's DLC package (an Xbox 360 LIVE file, content type 2: the autumn tale) here; installed at the first start."
}
if (Test-Path $elf) { Copy-Item $elf (Join-Path $out "ilomilo-nx.elf") }
Copy-Item (Join-Path $root "dist\switch\README.txt") $out
if ($Notes) { Copy-Item $Notes (Join-Path $out "PACKAGE_NOTES.txt") }
Push-Location $root
try {
    $sha = (& git rev-parse --short=12 HEAD).Trim()
    & git archive --format=tar.gz -o (Join-Path $out "source_$sha.tgz") HEAD
} finally { Pop-Location }
$md5 = (Get-FileHash -Algorithm MD5 (Join-Path $sd "ilomilo-nx.nro")).Hash.ToLower()
Write-Output "package: $out"
Write-Output ("NRO {0:N1} MB, md5 {1}; commit {2}" -f ((Get-Item (Join-Path $sd "ilomilo-nx.nro")).Length / 1MB), $md5, $sha)
Get-ChildItem -Recurse $out | Where-Object { -not $_.PSIsContainer } | Select-Object FullName, Length | Format-Table -AutoSize
