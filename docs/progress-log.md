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
- 01:58 First Switch NRO (43.0 MB). 02:06-02:11 emu2 (Ryujinx 330 s): boots, DLC installed, the title's assets load,
  but only 5 frames end on the render thread and no game-thread 10 s report comes (no Swap reached), while about
  8,100 game frames' draws arrive: no capture. Next: emu3 with the stall watchdog on (out/emu_tomls/emu_stall.toml).
- 02:30 tools/package_switch.ps1 made ilomilo's (names, ilomilo.toml from app/ilomilo_switch.toml, no forwarder NPDM).
- 02:41-02:45 emu3 (Ryujinx 200 s, stall watchdog): the main thread is busy in the game loop and drawing, never at
  the present; only 2 frames. The per-frame function sub_82193768 (its tail calls the present through slot 0x44 of
  the object at 0x82645070) and several copies on the drawing path are in-place bulk copies; the PC ran the same 90
  copies hooked and guarded at 60 fps. Next: every bulk copy `off` (out/localized_bulk_all_on.txt keeps the list),
  post_codegen with tools/keep_mtimes.py around it (only the copy shards rebuild), a Switch build and an emulator run.
- 03:02-03:20 emu4 (every copy off: same stall, copies cleared), emu5 (the diagnostic's std::thread: std::terminate on
  the Switch), emu6 (ilomilo_frame_diag with a pthread): the game loop runs ~500 frames/s and renders each frame, the
  present routine ran twice; the scene render presents only while the render device's suspended flag
  [0x826B71FC] is 0, so the device was suspended after frame 2 and never resumed. The diagnostic now logs each device
  Suspend/Resume with its caller and sub_82365B50's entry/exit; waiting for a slot. Handoff 4 (Ryujinx's rexglue logs
  in /switch/, the runner collects them) in D:\ilomilo\out.
- 04:00-04:25 emu8: TickCount advances; the logo's state 0 ends (to state 5) before a state-0 frame runs a second
  after it began, so the game's resume never comes. ilomilo_logo_hold_resume (on) resumes the device when the scene
  leaves state 0 still held. emu9 (full machine copies back): 55-60 fps, logo, menus, loading, prologue and the first
  level captured. A Switch-only fault remains: the top two tiles show the game's clear colour where the PC shows the
  backdrop (suspect: deko3d's colour hand-over); emulator-only runs with the hand-overs off queued.
- The user's new instruction (via the Ridge Racer 6 session): re-encode audio to Opus, the movie to H.265, and pack
  the files LZ4/ZXC. Started: the installer's XACT 3 reader (lib/xact3.js, container "xact"), game.json's audio
  section; all 435 XMA sounds (63.1 MB) qualify; startup.xwb (PCM) stays packed PCM.
- 04:30-05:00 Media: .xmop for the 8 XMA banks (63.0 -> 53.0 MB, checks OK), .opcm for startup.xwb (17.5 -> 1.9 MB;
  banjo's writer, byte-order guess fixed), the movie's H.265 (35.2 -> 13.4 MB) and its hook in the NRO source
  (ilomilo_wmv_ffmpeg.cpp, not built yet), packing lists measured. Handoff 5 (installer: XACT 3, .opcm). Picture
  fault: not an enhancement (all non-CPU items off, depth items off: same); draws are issued as on the PC; next a
  RenderDoc capture of Ryujinx. Waiting for Poker Smash's builds (slot after).
- 05:00-05:55 RenderDoc on Ryujinx (rdc_emu1): the depth-of-field rectangle lists lose triangles; keys tried, each in
  its own run (emu16-emu20): clip_disable honoured, rectangle depth clamp, depth bias off, bias fields off, fast draws
  and provisional pipelines off: the same wedges every time. The movie hook built (ilomilo_wmv_ffmpeg.cpp).
- 05:55-06:15 The cause found (tools/rdc_ms.py on the same capture): Ryujinx's translation of Renut's rectangle GS
  writes gl_ClipDistance[0] from the vertex shader's clip distance, which sasrt_gpu_clip_spec's vertex shaders (no
  plane: constant 929 = 0) never write. The console turns that clip slot off (plume noUserClip); Ryujinx clips with
  it. Fix: ilomilo_renut_gs_no_clip (on), no-clip variants of the rectangle and point-sprite GSs for those draws
  (usual GS byte-identical); compiled for SPIR-V, DXIL and deko3d by hand, commit 7249090f. Handoff 6 written
  (patch checked against the base's files). 32 machine copies added from the Ryujinx profiles of emu17-emu20
  (switch_hot_bulk.py --merge; ELF kept as out/elf/renut_14a84197.elf). Next, when Poker Smash's runs end: emu21
  (sasrt_gpu_clip_spec = false on the current NRO: the cause confirmed if the wedges go), post_codegen + Switch
  build, emu22 (the fix and the copies).
- 06:25-06:50 emu21 (sasrt_gpu_clip_spec off): areas of another shape, not gone (Ryujinx's GS carries clip distances
  1-3 too). post_codegen with the 32 copies (keep_mtimes: 91 files changed), Switch build 11 (5 min, NRO 45.8 MB),
  emu22: **the picture is whole in Ryujinx** (logo, title backdrop, loading card, the first level's sky), 56-60 fps.
  Handoff 6 completed with the results. 11 more copies from emu22's profile (136 on the list). Poker Smash has the
  machine (~40 min: PC build and run, Switch build, Ryujinx run).
