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

## 2026-11-25

- 00:08 First PC boot with Renut (D3D12, then Vulkan): title screen, 60 fps, self-checks 0 differences; only the top
  256 lines drawn. RenderDoc (out/rdc/title1): the scene's targets are 1280x256: ilomilo draws 720 lines with 4x MSAA in
  three predicated tiles. BeginTiling / EndTiling found at XDK 20209 (sub_82215D10 / sub_82216378) and hooked; the
  calls still went around the hooks (direct_calls.py) until post_codegen ran again: tools/hook_bypass_check.py written.
- 00:20 Menu flow from a scripted run (title, START, select a story, A through the story intro, the prologue card).
- 00:25-00:55 Switch side's game layer: ilomilo_switch*.toml, ilomilo.toml, the icon, version 0.1.0, the package tomls
  (tools/make_ilomilo_tomls.py) and README; Katamari's DLC pack list out. The calling-convention censuses clean. The
  register diet audited and turned on (keep list 125, two share_registers). The movie is the trial's upsell only.
- Poker Smash's first build (from 00:17) holds the build slot; my rebuild waits for its "done".
- 00:55-01:02 The diet build (8 min). 01:02 play1: the whole 720 lines (the tiling hooks reached), the first level
  played by the script; 60 fps, self-checks 0. 01:05 CG-13 census (300 s): no site that matters, ONE_MODE stays on.
  SMAA's composite found (0B4973CE2EEC601A, the depth-of-field pass): 600 frames per 10 s. The four log-decided keys
  set (no command buffers, nothing inert, no redeem). Audio stereo check: the centre keeps sound with stereo set:
  no saving. Handoffs 1-3 written in D:\ilomilo\out (gamma Flags at 5632, hook_bypass_check.py, installer deflate_raw).
- The installer copy (D:\ilomilo\ilomilo-nx-installer) made: ilomilo's game.json (title update and DLC), icon,
  the 16 shader records (tools/ilomilo_shader_records.py, checked by decoding).
