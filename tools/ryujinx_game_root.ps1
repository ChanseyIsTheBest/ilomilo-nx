# ilomilo-nx (2026-11-25): which game folder this port's emulator SD reads. sdmc:/switch/ilomilo-nx/game_root is a
# junction (the base's emulator setup): -Folder points it at another folder (the media test folder, a copy of the game
# with the installer's stand-ins: tools never pack the master copy in place, the base's media guide's trap 2), and
# -Restore points it back at D:\ilomilo\game. Only the link changes; neither folder's files are touched. Run it only
# when no Ryujinx runs.
#   powershell -File tools/ryujinx_game_root.ps1 -Folder D:\ilomilo\game_media
#   powershell -File tools/ryujinx_game_root.ps1 -Restore
param([string]$Folder = "", [switch]$Restore)
$link = "D:\New folder\ryu-data\ilomilo\sdcard\switch\ilomilo-nx\game_root"
$master = "D:\ilomilo\game"
if (Get-Process -Name Ryujinx -ErrorAction SilentlyContinue) { Write-Output "a Ryujinx is running: not changing the link"; exit 2 }
$target = if ($Restore) { $master } else { $Folder }
if (-not $target -or -not (Test-Path $target -PathType Container)) { Write-Output "no folder '$target'"; exit 3 }
$item = Get-Item $link -ErrorAction SilentlyContinue
if ($item -and -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { Write-Output "$link is not a link: not touching it"; exit 4 }
# Removing a junction removes the link only (cmd's rmdir on a junction does not recurse into its target). Windows' own
# cmd by its full path: started from Git Bash, PATH finds msys2's `cmd` first (the first try failed there, harmlessly).
if ($item) { & (Join-Path $env:SystemRoot "System32\cmd.exe") /c rmdir "$link" | Out-Null }
if (Test-Path $link) { Write-Output "the link could not be removed: not changing it"; exit 5 }
New-Item -ItemType Junction -Path $link -Target $target | Out-Null
Write-Output ("game_root -> {0}" -f (Get-Item $link).Target)
