<p align=center><img src="tools/switch/icon/ilomilo_icon.jpg" alt="ilomilo" width="256" height="256"></p>

<h1 align=center>ilomilo: Nintendo Switch port</h1>

<p align=center><b>ilomilo-nx 1.0.0</b> · <a href="https://chanseyisthebest.github.io/ilomilo-nx-installer/">web installer</a> · <a href="https://github.com/ChanseyIsTheBest/ilomilo-nx/releases/tag/v1.0.0">release</a></p>

An unofficial, native Nintendo Switch port of the Xbox Live Arcade game **ilomilo** (SouthEnd Interactive and Microsoft
Studios), recompiled from the code of its Title Update #1 with [ReXGlue](https://github.com/rexglue/rexglue-sdk) and
drawn by reNut's Direct3D-level renderer on deko3d. It is not an emulator.

There are no game files in this repository. You need your own copy of the game:

- the Xbox Live Arcade package (the `LIVE` file in `58410A1B/000D0000/`, or a folder you extracted it to),
- **Title Update #1** (content type `000B0000`): the port is built from the update's code, so it is required,
- optionally the "autumn tale" downloadable content (content type `00000002`).

## Playing it on the Switch

1. Open the web installer: **https://chanseyisthebest.github.io/ilomilo-nx-installer/**
2. Give it the game, Title Update #1 and, if you have it, the DLC, then press **Create ilomilo-nx.zip**. Everything is
   made in your browser; your files are not uploaded anywhere.
3. Extract `ilomilo-nx.zip` into `sdmc:/switch/` on your SD card.
4. Start it through a title override (hold **R** while starting an installed game) or a forwarder. The Album applet
   does not give the game enough memory, and a forwarder needs a 39-bit address space.

On new screens the first session can stutter briefly while shaders compile (unless the installer compiled them, its
default); later sessions start smoothly.

## What you get

- The full game (not the trial), with Title Update #1 and the DLC when you add it.
- Two players: each controller is the player its lights show (the handheld or controller 1 is player 1), and further
  controllers sign in on their own as "Player 2" to "Player 4", so the second player just presses A on the
  "play together" screen.
- Face buttons by position, as on the Xbox 360 pad (`input_xbox_layout = false` for by letter); button maps per player
  (`[input_p1]`, `[input_p2]`); single Joy-Cons held sideways, one per player.
- 1080p docked and 720p handheld; SMAA on and MSAA off by default (`msaa_level = 2` or `4` for the game's own 4x MSAA).
- Optimised for the console: profile-guided and link-time optimisation trained on a play session on real hardware, and
  optimised copies of over a thousand of the game's busiest functions.
- Smaller files from the installer: the music and voices re-encoded to Opus, the game's archives packed with LZ4, and
  the trial's upsell movie left out (an option; the full game never shows it).
- Your settings in `ilomilo.toml` next to the NRO (delete it to get the defaults back).

## Building

You need Windows with LLVM clang and the Visual Studio Build Tools (the PC test build), devkitA64, libnx and deko3d from
[devkitPro](https://devkitpro.org) (the Switch build), Python, and your own copy of the game for the code generator and
the shaders. [docs/building.md](docs/building.md) has the steps; `tools\ilomilo_build_switch_final.bat` builds the
released NRO (with the profile in `pgo-inplace/`). The port's own notes are in [docs/ilomilo-notes.md](docs/ilomilo-notes.md)
and [docs/progress-log.md](docs/progress-log.md); the shared base this port starts from is described in
[docs/renut-ultimate-base-README.md](docs/renut-ultimate-base-README.md).

## Credits

- **SouthEnd Interactive and Microsoft Studios**: ilomilo. This is an unofficial fan port.
- **ChanseyIsTheBest**: this port, its installer and the renut_nx_ultimate base it is made from.
- **[Tom Clay](https://github.com/rexglue/rexglue-sdk)**: the ReXGlue SDK, built on the work of the
  **[Xenia](https://xenia.jp)** team.
- **reNut and [masterspike52](https://github.com/masterspike52/reNut)**: reNut's Direct3D-level renderer (reused with its
  author's permission); reNut's own contributors are credited in [app/README.md](app/README.md).
- **[StevensND](https://github.com/StevensND/nfsmw-nx)**: nfsmw-nx, the Switch layer of the SDK and much of the method,
  and nfsmw-nx-installer, which the installer page grew from.
- **[nebadasSwifty](https://github.com/nebadasSwifty/masseffect-nx)**: masseffect-nx.
- **[hedge-dev](https://github.com/hedge-dev/XenosRecomp)**: XenosRecomp, the Xenos shader translator.
- **[plume](https://github.com/renderbag/plume)** (from UnleashedRecomp), **[deko3d](https://github.com/devkitPro/deko3d)**
  and **[uam](https://github.com/devkitPro/uam)** by fincs, with SwitchWakerHD's uam patches.
- **[devkitPro](https://devkitpro.org)** and **[switchbrew](https://github.com/switchbrew/libnx)**: devkitA64 and libnx.
- **[KhronosGroup](https://github.com/KhronosGroup/SPIRV-Cross)**: SPIRV-Cross.
- The ports whose fixes the base gathers, listed in [docs/renut-ultimate-base-README.md](docs/renut-ultimate-base-README.md),
  and the other libraries in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Legal

Not affiliated with or endorsed by Microsoft, SouthEnd Interactive or Nintendo; ilomilo is a trademark of Microsoft. This
repository holds no game files and no code generated from the game: you provide your own legally obtained copy, and
everything made from it (`app/generated/`, the shaders, the installer's package) is made on your own computer. Running
homebrew needs custom firmware, which breaks Nintendo's terms of service and can get a console banned.

The source code is under the GPL-3.0 License ([LICENSE](LICENSE)), like the ports it builds on; the SDK keeps its
BSD-3-Clause license ([THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)).
