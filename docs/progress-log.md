# ilomilo-nx: progress log

Times are AEST. The session runs until 23:04 on Wednesday 25 November 2026; no console work until the user says so.

## 2026-11-24

- 23:07 Start. Read the base's README, building.md, porting prompt, katamari-notes (code generation and Renut
  sections), xdk-notes, renut-nx's porting-start-here, porting-guide-renderer, title-update-3 and xdk-versions.
- 23:10 Extracted the game (439 entries, 247.4 MiB), the title update (default.xexp) and the DLC (39 entries) with
  tools/stfs_extract.py. XDK 2.0.20209 (the same build as Bangai-O HD).
- 23:20 ilomilo-nx created from the base's files at 680dee40 (git archive, no history); first commit.
- 23:25 Code generation on the patched image (TU1: 0.0.0.2 -> 0.0.1.2): seven split type checks fixed; pointer sweep
  73, gap sweep 62, one built callback; jump tables clean; setjmp / longjmp found.
- 23:35-00:00 Katamari's game layer taken out (hot lists, movie hook, stage diagnostic). Renut's 313 Direct3D hooks
  moved to ilomilo through bangaio-nx's N&B -> Bangai-O map and a Bangai-O -> ilomilo pairing; signatures checked
  (the locks' unused argument, the gamma Flags). The device layout measured (Katamari -> ilomilo zones) and found to
  be Bangai-O's; the guest data addresses found; the rewrite prepared (applied after the first build).
- Shaders: 83 containers in the image, 135 more in startup.par's effects.
- First PC build: missing pieces of a fresh copy found one by one (the DXC binaries, the shader dump before the
  build, glslang and the deko3d host tools in out/: all copied from the base's working tree, which git ignores).
- Ryujinx data folder `D:\New folder\ryu-data\ilomilo` made (bis, system, profiles, Config.json from katamari's; its
  own SD with `switch\ilomilo-nx\game_root` -> D:\ilomilo\game and `dlc` -> the DLC package's folder).
