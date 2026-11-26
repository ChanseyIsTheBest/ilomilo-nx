<p align=center><img src="tools/switch/icon/ilomilo_icon.jpg" alt="ilomilo" width="256" height="256"></p>

<h1 align=center>ilomilo: Nintendo Switch port</h1>

<p align=center><b>ilomilo-nx 1.0.0</b> · <a href="https://chanseyisthebest.github.io/ilomilo-nx-installer/">web installer</a> · <a href="https://github.com/ChanseyIsTheBest/ilomilo-nx/releases/tag/v1.0.0">release</a></p>

An unofficial native port of the Xbox Live Arcade game **ilomilo**, made by static recompilation with
[ReXGlue](https://github.com/rexglue/rexglue-sdk). No emulator.

This repository contains no game files. You need your own copy of the game and its Title Update #1.

## Playing it on the Switch

1. Open the web installer: **https://chanseyisthebest.github.io/ilomilo-nx-installer/**
2. Give it your game package or extracted game folder, Title Update #1, and the "autumn tale" DLC if you have it.
3. Extract the `ilomilo-nx.zip` it downloads to the root of your SD card and follow the page's steps.

Features:

- The full game with Title Update #1; "autumn tale" DLC supported.
- Two-player co-op: connect a second controller and press A on the "play together" screen.
- Native Switch renderer: 1080p docked, 720p handheld, with SMAA.
- Optimised with PGO and LTO; music and voices in Opus and the game files packed smaller.
- Logging off except crash reports. For a bug report, set `log_level = "info"` at the top of
  `switch/ilomilo-nx/ilomilo.toml` and send the `switch/ilomilo-nx/logs/` folder.

## Building on Windows

Needs the VS Build Tools, LLVM clang, Python 3 and devkitPro (devkitA64, libnx, deko3d), plus your own copy of the
game. The steps are in [docs/building.md](docs/building.md); `tools\ilomilo_build_switch_final.bat` builds the released
NRO. More in [docs/ilomilo-notes.md](docs/ilomilo-notes.md).

## Credits and license

Built on ReXGlue, Renut (reNut by [masterspike52](https://github.com/masterspike52/reNut), used with permission), plume
and deko3d; method and tools from [nfsmw-nx](https://github.com/StevensND/nfsmw-nx),
[masseffect-nx](https://github.com/nebadasSwifty/masseffect-nx) and the ports of the renut_nx_ultimate base. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

GPL-3.0 (see [LICENSE](LICENSE)); the SDK keeps its BSD-3-Clause license. No affiliation with Microsoft, SouthEnd
Interactive or Nintendo.
