# ilomilo port: notes

This file records the port: what each step found, with its evidence. The project is a copy of the ultimate base's
files (renut_nx_ultimate_base 680dee40, `D:\renut-ultimate\base`, read-only; no history), which builds Beautiful
Katamari as checked in. Comments that say "katamari-nx", "banjo-nx", "bangaio-nx", "blur-nx", "sasrt-nx" and so on
record findings from those ports.

The user's request (2026-11-24, 23:04 AEST): port ilomilo to the PC and the Switch with ReXGlue from the ultimate
base, the Switch the main goal; work uninterrupted until 23:04 AEST on Wednesday 25 November 2026; no console work
until the user says so in this session (PC and Ryujinx only).

Credits: Renut's renderer (masterspike52's reNut; its author permits reuse in the user's ports), the ultimate base and
the ports whose fixes it carries (its README, THIRD_PARTY_NOTICES.md and docs/ultimate-fixes.md name them), renut-nx,
sa2-nx, NetherSX2_nx, battd_nx and the bejeweled3-nx / zuma ports. GPL-3.0 where the sources are. Game data is never
committed or distributed.

## Where it stands (2026-11-25, 12:30: the user stopped the work after rc3)

- **For the console:** rc3, D:\ilomilo\builds\2026-11-25_1222_rc3_console_PERSONAL (the user's own console only:
  game data inside): the release NRO (1,132 machine copies in place, no game shader inside, no PGO / LTO, NRO md5
  f2d01c92...), deko3d_glsl.bin as its own file, the shader cache, ilomilo.toml with profiling on
  (dist/switch/ilomilo_profiling.toml), the game files with Title Update #1, the DLC, READ_ME_FIRST.txt. rc1 is
  superseded (it has the copy the guard rejected); rc2 (D:\ilomilo\builds\2026-11-25_1117_rc2, no game data) is
  the last plain package; the web installer's release is 0.1.1 (rc2's NRO).
- **Checked on the PC and in Ryujinx (never on a console):** the full game boots, plays its menus, the prologue and
  the first level at 60 fps on the PC and 59-60 in Ryujinx; the copies against the generated code: 0 differences
  (verify5); Opus sound plays; the Switch-only picture fault fixed (ilomilo_renut_gs_no_clip).
- **Next (the console):** the picture, the sound and the speed on real hardware; a console profile from rc3 (for the
  hand-written natives); the H.265 upsell movie (trial only, untested); sub_820B3F90's guard difference (kept out).
- **The user's decisions waiting:** PGO + LTO; the music at 96 kbit/s (about 11 MB less).
- **Handoffs for the base:** D:\ilomilo\out (README.md lists the 7).

## The first console run (2026-11-25, 17:56-18:00, rc3 with profiling on; the user)

The user ran rc3 on the console and asked for its screenshots, videos and logs over FTP and for a CPU and GPU
breakdown (out/console_runs/con1/breakdown.md has the tables; the files are there too, game screenshots included:
never committed). The console's address went into out/switch_host.txt (the console's address on the home network) and the
port's folder into out/switch_sd_root.txt (/switch/ilomilo-nx); the Album is on the emuMMC (/emuMMC/RAW1/Nintendo/
Album), read only.
- **It runs:** 58-64 fps in the menus, loading and the first level (handheld clocks), CPU 38-119 % of the 400 %
  scale, GPU 8.3-11.4 ms a frame, 179 MB of GPU memory.
- **Game thread** 30 % of a core on average (41-48 % in the level), 62 % of it in machine copies; **Opus decoding**
  up to 20 % of a core in the level (DecodeXmoFrame and libopus); the **render thread** 0.9-4.5 ms a frame.
- **Vertex explosions** in the backdrop behind the menus, the prologue map and the loading cards (the level and the
  UI are right); console only (the same NRO is clean in Ryujinx and on the PC); nothing in the log. Suspect: vertex
  reads past a buffer's end (zeros in Ryujinx's Vulkan, memory on the console). Next: a console test.
- **The investigation (18:10-19:20).** The explosions were in the emulator too and I had missed them: emu27, emu31,
  emu32, emu33 (the release NRO with the player's settings) show them; emu22 / 25 / 26 (the verify test toml) and the
  everyday NRO do not. But five reruns of exactly emu27's setup this evening (rel_none2, rel_A2, rel_p10, rel_A10,
  rel_B10) were clean: not the settings, not the shader package (byte-identical to the built-in one, the tables equal
  in every field deko3d reads), not the build options (only the shader paths differ), not the DKSH cache or pipeline
  list (unchanged since 07:16), not the game-folder index, not the emulator (unchanged since 2026-11-10). What is left
  is a race. rr6_frames_ahead = 1 (the default) lets the game build frame N+1 while the render thread converts frame
  N, and Renut reads the game's vertex buffers when the render thread reaches a draw: a dynamic buffer the game
  rewrites for the next frame (the menus' and loading cards' animated backdrop; the level is mostly static) can be
  read half-written. The console's render thread lags more, so it shows there every time; in Ryujinx it depends on
  the load. sasrt-nx saw its skinned models explode the same way with one frame ahead. (rr6_diag_render_delay_ms = 10
  to provoke it in Ryujinx stalled the game: no answer.)
- **The console test (19:25, the user: "Ftp it over"):** `rr6_frames_ahead = 0` added to the card's ilomilo.toml
  (profiling kept; out/console_runs/ahead0 has the before / after files). The user opens the menu and a loading card.
  If clean, the fix is for the renderer to copy those vertex buffers when the draw is queued (keeping one frame ahead).
- Found on the way (sonic racing's finding of SASRT's release-shader bug): draw.cpp's tile-twin check read
  g_shaderLiterals at a merged-table offset; now g_activeShaderLiterals. Not this bug (the tile-twin merge takes only
  tessellated draws; ilomilo never logs one), but wrong with any installed version-2 package: a base handoff.
- **Result (the user, ~20:00): "Frames ahead 0 fixes it performance is still good".** rr6_frames_ahead = 0 is now the
  default: app/ilomilo_switch_defaults.toml (built in) and tools/make_ilomilo_tomls.py's SHIPPED (every dist toml),
  commit b2594c77.

## Multiplayer (2026-11-25, 20:10-21:20; the user: player 1 "not signed in", player 2 could start, player 1 not join)

Three faults, each in the SDK, and a crash the fix uncovered. rc4 (D:\ilomilo\builds\2026-11-25_2118_rc4) has them.
- **The controller order (the console's log, out/console_runs/mp_user/renut_003.log).** The game started in handheld
  mode (handheld = player 1); a Pro Controller connected as No1 and became player 2; then the Joy-Cons came off as No1
  and the Pro Controller moved to No2. Guest users followed the order controllers connected in, so the user's player
  1 (Joy-Cons, the Switch's No1) was Xam user 1 and the Pro Controller user 0. Now `input_switch_player_numbers` (on):
  a Switch controller is the player the Switch numbers it (handheld and No1 player 1, NoN player N; DeviceInfo's new
  player_number, InputSystem::RefreshDevices); contested (handheld and No1): the holder keeps it; with nobody on player
  1, the lowest-numbered controller is player 1.
- **Nobody but user 0 signed in.** ilomilo's controller poll (sub_821C9418, through a vtable) skips a controller whose
  bit is not in the signed-in mask (0x824B3308, set per screen; all users on "play together"), and the game never
  opens the sign-in screen, so the SDK's guests (port 55) never signed in. hexic2-nx's xam_guest_signin_on_connect
  (its commit 97109a5a) taken, on here, and asked from XamUserGetSigninInfo too (ilomilo polls it for users 1-3 each
  frame with flags 1 and 2).
- **No guests as players.** The multiplayer page (MultiplayerPage, vtable 0x8200C0A0, its input handler
  sub_82142428: event 210 = A, the user index) shows the sign-in message for a player whose user record word 72 is 0
  (record array 0x826452C0, 104 bytes a user, filled by sub_821A7988 / sub_821A7B28 from XamUserGetSigninInfo: word
  72 = not a guest, 76 = signed in to Live, 84 = guest, 88 = not Live-enabled). So `xam_guest_profiles` (on): players
  2-4 are local profiles of their own ("Player 2", no guest flag, their XUID as before), their profile setting writes
  succeed (not stored).
- **The crash it uncovered: graphics memory gone after two minutes with two players.** The PC ran out of guest
  physical memory (MmAllocatePhysicalMemoryEx of 16 KB failed, then a call through 0) after about two minutes on the
  story cards or the prologue's level card. The census (`ilomilo_physical_census`, resource.cpp's AllocPhysical /
  FreePhysical): 16 KB allocations growing by 240 a second, never freed, from player 2's sign-in. The picture loader
  sub_821E4AF8 makes a 64x64 texture (16 KB) and asks XamReadTileToTexture (sub_822755B8: type 2, title 0, tile 0,
  the user index) for the player's own picture; the SDK refused tile 0, the loader set "not loaded" and tried again the
  next frame with a new texture, the last one never freed. Types 2-5 with tile 0 for a signed-in user now succeed (a
  blank picture; nothing shows it on these screens). The single-player control (a fresh profile, three minutes on a
  story card) never leaked: only two players' pictures are asked for.
- **PC checks** (mp7-mp12, input_script_p2): player 2 joins (milo "Player 2", "A start"); two players through the
  story cards, the level card and loading into the prologue level at 60 fps; two minutes on the level card with no
  growth and no crash.
- **The console (21:50-22:09, the user: "It's awake now"; rc4's NRO on the card, rc3's kept as ilomilo-nx_rc3.nro).**
  Player 1 the handheld, driven by input_script in a test toml (the user's own ilomilo.toml put back after, byte for
  byte; a copy stays as ilomilo_user_backup.toml); player 2 sys-botbase's virtual Pro Controller (the Switch's No1).
  The log: "handheld is player 1", "Pro Controller (No1) is player 2", signed in as "Player 2" in the first frame.
  Player 2 joined (milo "Player 2", "A start"), the story cards, the prologue's level card, loading and the level at
  60 fps, player 2's stick walked milo; no error, no crash (out/console_runs/mp_rc4, renut_005-007.log). Two traps:
  the user's input_xbox_layout = true makes the Switch's B the game's A (sys-botbase's "A" was player 2's back);
  the story cards take "continue" from player 1 only (the game's own rule: player 2's A never advanced one).

## Decisions (made without asking, as the request said)

| What | Decision | Why |
|---|---|---|
| Game files | the LIVE package extracted with `tools/stfs_extract.py` into `D:\ilomilo\game` (439 entries, 247.4 MiB) | the request |
| Title update | `D:\ilomilo\update\default.xexp` (one file), copied beside `default.xex` in `D:\ilomilo\game` | the SDK applies a sibling `<xex>p` when it loads the executable (sdk/src/system/user_module.cpp), for the code generator as for the game, so the generated code is the update's |
| DLC | "autumn tale" extracted into `D:\ilomilo\dlc` (39 entries, 14.9 MiB: `dlc1.par`, `Data\sound\Xbox\dlc1.xwb/.xsb`); the package itself is what the base reads in place from `dlc\` (port 265) | the request |
| Port folder | `D:\ilomilo\ilomilo-nx`, git, local commits only (the user's GitHub noreply address) | the request |
| `app/assets` | a junction to `D:\ilomilo\game` | no second copy on a shared D: drive |
| Internal project name | `renut` (as the base) | the base's CMake, passes and renderer glue name `renut_*` files and targets; the NRO, its title and the SD folder are ilomilo-nx |
| SDK host binaries | the base's `sdk/out/win-amd64` (rexglue.exe and the SDK libraries, built from the same SDK sources at 680dee40) copied in for the first code generation | `tools/codegen.ps1` needs `rexglue.exe` before the first PC build makes its own |
| First boot | the SDK's emulated GPU, Renut compiled out (`tools/build_pc.bat`'s default `RENUT=OFF`) | separates CPU / kernel problems from renderer problems (katamari-nx's and peggle2-nx's order of work); Renut's Direct3D hooks are at Katamari's XDK 2.0.5632 addresses and must be moved to ilomilo's 2.0.20209 first |
| Register diet (codegen) | off for the first code generation (`non_volatile_as_local`, `elide_lr_stores`, `non_argument_as_local`) | each needs this game's own audit first (katamari-nx's order) |
| `ilomilo_logo_hold_resume` | on | the logo's suspend was never resumed when the first frames were slow (the emulator's stall); it resumes only the device the game itself suspended, at the moment the game's own code would have |
| `ilomilo_renut_gs_no_clip` | on | the console's pixels cannot change (the clip slot was already off for those draws); it removes Ryujinx's wedges and a few outputs a vertex |
| `ilomilo_renut_clip_disable`, `ilomilo_renut_rect_depth_clamp` | built, off | tried for the wedges, neither changed the picture; left off so the default is the base's clipping |
| Hot functions from Ryujinx | 32 more machine copies (emu17-emu20) | the request: machine copies from every profile, Ryujinx included; hand-written natives wait for console data |

## The game (2026-11-24)

- Package: `Ilomilo\58410A1B\000D0000\D2BAC6E5...`, LIVE, content type 0x000D0000 (Xbox Live Arcade), title
  **58410A1B**, "ilomilo", 63,596 blocks: 439 entries, 247.4 MiB. 359 `.dds` textures (90.6 MB), 9 XACT wave banks
  (80.5 MB; `.xsb` sound banks and one `.xgs`), the movie `Data\media\upsell.wmv` (35.2 MB), 6 TrueType fonts in
  `Media\` (18.8 MB), five `.par` archives in `Data\` (16.2 MB: `arch0`-`arch3.par`, `startup.par`) and
  `archcache.pca`, `IloMilo.ini` (`Render=XenonRender.XenonRenderDevice`, `Sound=XactSound.XactSoundDevice`,
  1280x720, `DataPath=game:\data\`).
- **`default.xex`** (`tools/xex_info.py`): original PE name `IloMilo.exe`, base `0x82000000`, entry `0x82273C10`,
  image `0x740000`; encrypted and compressed. Imports `xam.xex` (152) and `xboxkrnl.exe` (296) at 2.0.20209.
  Static libraries: XDK **2.0.20209** QFE 0 (D3D9, D3DX9, XGRAPHC, XAPILIB, XAUDIO2, XAPOBA, X3DAUD, XBOXKRNL, XUIRUN,
  XUIRNDR, XACT3, XNET, XONLINE, XHV2, XPARTY, XMP, LIBCMT, XMCORE, XAUD), MSVC 16.0.10224. The same XDK build as
  Bangai-O HD and Bejeweled Blitz LIVE (renut-nx's docs/xdk-versions.md; Bangai-O's D3D9 / XGRAPHC are QFE 3).
  Execution info: media 2F5D19C7 (the title update's folder name), version 0.0.0.2.
- **Title Update #1** (`TU_1C422GR_0000008000000.0000000000082`, LIVE, content type 0x000B0000, title 58410A1B):
  one file, `default.xexp` (323,584 bytes). The SDK applies it: "XEX patch applied successfully: base version:
  0.0.0.2, new version: 0.0.1.2". Patched image: base 0x82000000, size 0x740000 (the same as the base game's, so the
  function table under the image needs no rewrite: "0 function table entries written again"); code
  `0x820B0000-0x824A6B44` (generated REX_CODE_BASE / SIZE).
- **DLC "autumn tale"** (LIVE, content type 0x00000002, 3,828 blocks): `dlc1.par` (6.6 MB), `Data\sound\Xbox\dlc1.xwb`
  (7.6 MB) and `dlc1.xsb`, `spa.bin`, its artwork and `ArcadeInfo.xml` (15 achievements).

## Code generation (2026-11-24)

- `tools/codegen.ps1` (the base's `rexglue.exe`): 7.3 s, 147 files (75 MB) in `app/generated`.
- **First run**: seven "Unresolved conditional branch to T from T+0x14". Each is a 16-instruction type check
  (`IsA(r4)`: two compares returning 1, then `return r4 == 0x82003CC0`) that the scanner ended at its first `blr`;
  declared over the whole 0x40-byte body in `app/config/renut_funcs.toml`. Second run: clean.
- **Pointer sweep** (`tools/pointer_fixpoint.py`): pass 1, 6,162 gaps, 74 candidates, **73 accepted** (vtable and
  callback-table entries, three "built at" callbacks, none 0x14 after its build), 1 rejected (a fragment); pass 2
  fixpoint.
- **Gap sweep** (`tools/gap_sweep.py`): 6,119 gaps, 142 candidates, **62 accepted** (53 extended beyond their gap, 27
  no code); fixpoint after one pass.
- **Jump tables** (`tools/switch_check.py --code 820B0000:824A6B44`): 548 `bctr` (450 indirect, 77 absolute, 8 byte,
  13 half), 98 switches generated; truncated 0, wrong targets 0, missed 0, no bound 0. One odd shape: `bctr
  0x82329B40` switches on `r4 & 0xFFFF` with no bound in the code, through an inline table at 0x82329B44; the
  generator made 22 cases, which is the table's length (it ends where the first case's code starts, 0x82329B9C).
- **Built pointers** (`tools/built_ptr_scan.py`, port 191): one, `0x82321008`, built at `0x823211C4` by the
  constructor `sub_823211B8` and stored at +0 of its object: a callback reading r3-r5, declared in
  `app/overrides.toml`. Then 0 candidates.
- **setjmp / longjmp** by shape: setjmp `0x8243B6D0` (a hook word at `0x826E4454` tried first, `bnectr`, then `mflr`,
  `mfcr`, `stfd f14,0(r3)`: the only one), longjmp `0x8243B290` (`mr r6,r4`, the check of +312, `mr r7,r3`, `lfd
  f14,0(r7)`: the only one). The same shapes as Bangai-O's.
- 12,815 functions registered (8,649 in `.pdata`).

## The calling convention (2026-11-25, step 2)

On the generated tree after post_codegen in full:
- `tools/cc_entry_census.py`: 12,597 functions, 228 read a vector register on entry (non-volatile v14-v31 and
  v64-v127 save / restore helpers' shapes, v1-v4 arguments); 4,265 pointer-reached functions, **"reading v0 or
  v32-v63 on entry (must be none): none"**.
- `tools/cc_exit_census.py`: **8,022 indirect call sites, 0 with a register of EXIT_DEAD read after the call.**

So the machine copies' register liveness keeps the base's defaults (`SASRT_REG_LIVENESS_EXIT_ABI` and `_HOOKS_ABI`
on); no `scratch_vectors_read_on_entry.txt`.

## The register diet (2026-11-25)

The three codegen keys the first code generation left out, audited as katamari-nx did, on scratch code generations
(`out/audit/manifest_gen*.toml`: the app's config with absolute paths, out of the tree) without them (`gen`) and with
them (`gen2`, then `gen3` with the marks):

- `non_volatile_as_local`: `tools/read_before_write.py out/audit/gen2 --noreturn=8243B290`: 16 functions. setjmp and
  its three callers (the jump buffer's `env.r* = r*` copies: the codegen's setjmp handling); two `xor r30,r30,r30`;
  one `subfe` of one register; XDK code reading v64-v72 that nothing in the game sets (`non_volatile_as_local_keep =
  ["v64-v127"]`, the base's range for the video codec); two software-pipelined vector loops reading v14-v24 at their
  loop heads (`sub_8241A8D0`, `sub_8241B270`): `share_registers`, so they read the caller's registers as on the
  console. On `gen3` (`--volatile`): only the setjmp caller `sub_82254F48`.
- `elide_lr_stores`: every `mflr` in the code (53): prologue saves (MSVC's unwind funclets save it a few instructions
  in), setjmp / longjmp, and four C runtime helpers that keep it in r31 and put it back before their `blr`
  (`sub_82444400`, `sub_8244C7C0`, `sub_8244C86C`, `sub_8244C890`). Generated returns do not read the link register.
- `non_argument_as_local`: `tools/non_argument_audit.py out/audit/gen --noreturn=8243B290`: ENTRY 339, RET 15,
  HANDOVER 0. The save / restore helpers are kept by name by the generator; the other 124 (MSVC unwind funclets that
  take their frame in r12, a vector family saving v32-v63 through `sub_8245CD60` / `sub_8245D0A8`, the RET ones) are
  `non_argument_as_local_keep`, plus the setjmp caller `sub_82254F48`. On `gen3` (`--with-option`): ENTRY 340, RET 6,
  HANDOVER 1: `sub_82240A18` (a setjmp caller) calling `sub_82254F48` without r11, the jump buffer's copy of a
  volatile register (katamari-nx's "only the setjmp lines").

## The base's game layer taken out (2026-11-24)

- Katamari's hot lists (`app/src/cpu/hot/localized.txt`, `localized_bulk.txt`, `hand.txt`) emptied; its stage
  diagnostic (`katamari_stage_diag.cpp`) and movie hook (`katamari_wmv_ffmpeg.cpp`, Katamari's addresses) not built;
  the build stamp's game name and the Switch's fallback NRO path are ilomilo-nx's.
- `tools/ilomilo_hook_collisions.py` (new): every hook in `app/src` that names a guest function by address, against
  this game's function table. Of 468, two are at a function start of ilomilo, both N&B's widescreen hook in Renut's
  tree (`renut_engine/gpu/guest/widescreen.cpp`, `sub_821D55E8`); the rest name no ilomilo function (the link
  catches those that are built). The widescreen and photo hooks are compiled out (`KATAMARI_BANJO_ADDRESS_HOOKS`).

## Renut's Direct3D hooks at ilomilo's addresses (2026-11-24)

The base's hooks are at Beautiful Katamari's addresses (XDK 2.0.5632); ilomilo is XDK 2.0.20209, the same build as
Bangai-O HD, which bangaio-nx ported Renut to (from banjo-nx's N&B base-game addresses). The route, per hook line
(`tools/renut_hook_remap_ilomilo.py`):

1. the base's note `katamari-nx: N&B sub_X` names the function in N&B's title update 3;
2. banjo-nx's base -> update function map (`D:\Banjo kazooie port\tu_v3\map\func_map.json`, 32,830 functions),
   inverted, gives N&B's base-game function;
3. bangaio-nx's `out/renut_map/nb_to_bangaio_final.json` (three reference ports agreeing) gives Bangai-O's;
4. `tools/d3d_propagate_ilomilo.py` pairs Bangai-O's functions with ilomilo's: the two state tables (Bangai-O
   0x824A3460 / 0x824A3920 -> ilomilo **0x824B4440 / 0x824B4900**, found by Bangai-O's default columns word for
   word), unique shapes and aligned calls: 5,613 pairs, 2 conflicts dropped;
5. a second route by name: bangaio-nx's own hook lines (`// D3D name`), for the hooks it placed by hand (CreateDevice,
   Present, Release, UnsetAll, CBlocker_Check, GetSubresourceLayout ...);
6. six by hand (`MANUAL`, each with its evidence: `tools/d3d_best_match.py` against Bangai-O or the base's Katamari
   image, then read): VertexBuffer_Unlock `82211068`, CreateIndexBuffer `82211078`, the unlock after it `82211128`,
   InsertCallback `8221DFE8`, Acquire / ReleaseThreadOwnership `8220E408` / `8220E448`.

Result: **313 hooks placed, 13 hooks Katamari left unhooked turned on** (each is one bangaio-nx hooks at 20209:
SetRenderTarget's thunk, GetRenderTarget, GetDepthStencilSurface, GetStreamSource, GetViewport, SetClipPlane,
BeginExport / EndExport, DrawIndexedVerticesUP, XGRegisterPixelShader, AllocateInlineData, BlockOnFence,
GetDevice; plus Get2DSurfaceDesc's thunk and GetGpuTextureDimensions), 21 not placed (not linked by ilomilo: the B / I
constant setters, IndexBuffer_Lock, GetCubeMapSurface, GetVolumeLevel, the tessellated draw, the tiling functions,
BeginRingManual; SetTexture's inline copy, which Katamari has and ilomilo has not: `tools/d3d_best_match.py` finds
SetTexture `82210A38` and nothing else of its shape in the whole code), 19 left unhooked as in the base.
EndIndexedVertices (`82216AC0`: `lwz r11,13652(r3); stw r11,48(r3); blr`, Ring = VerticesRingEnd and no kick) stays
unhooked: on Renut's device it does what the hook would. No D3DVertexShader_Bind: no function but SetVertexShader
writes the device's vertex shader word (+12872), and `sub_822136F0` is SetFVF (it builds the device's own declaration
at +12368).

**Signatures** (`tools/arg_regs_compare.py`: the registers r3-r10 / f1-f13 each hooked function reads before writing
them, Katamari's against ilomilo's; 308 the same):
- D3D_LockResource `82211BC8`, D3D_LockSurface `8220FCB8` and D3D_Lock2DSurface `8220FD90` keep the first release's
  unused second argument (Lock2DSurface reads r3, r5-r9 and calls LockSurface with r4 passed through); the base's
  `xdk-notes.md` has it from 11164, bangaio-nx's hooks take it. New wrappers `LockResource_unused_hook`,
  `D3D_LockSurface_unused_hook`, `D3D_Lock2DSurface_unused_hook` (resource.cpp) are bound there. Lock3DSurface keeps
  the base's form.
- SetGammaRamp `8220CBE8` / SetPWLGamma `8220CCD0` take (device, Flags, ramp): the ramp is r5 (`mr r4,r5` before
  the copy). Bound to the base's `_flags_hook` forms. (Katamari's read r3 and r5 too, and the base binds the
  two-argument forms there: a possible base fault, noted for the handoff.)
- D3DDevice_Resolve `8221C450` is a wrapper of an internal resolve `8221B300` with two extra zero arguments (as
  rehatched-nx found at 9407); the internal one has no other caller, so the wrapper's hook sees every resolve.
- BlockOnFence `8221CC60` reads one more register (r7, a flag byte); the hook does not need it. VertexBuffer_Lock
  reads no size (r5). The other differences are the prologue's save-helper call.

## The device layout (2026-11-24)

`tools/device_offset_votes.py`: over the 307 paired functions (Katamari's hook address -> ilomilo's), aligned D-form
loads and stores vote "Katamari offset -> ilomilo offset" (`out/renut_map/device_votes.txt`). The zones
(`tools/renut_device_offsets_ilomilo.py`):

| Katamari | ilomilo | Evidence |
|---|---|---|
| 0 .. 10943 | the same | 149 offsets voted, all 0 (ring, state calls, fetch constants, packets, fences, flags) |
| 10944 .. 11811 | +12 | 10996 -> 11008, 11000 -> 11012 |
| 11812 (vertex declaration) | +180 (0x2ED8) | SetVertexDeclaration; bangaio-nx 0x2ED8 |
| 11813 .. 13183 | +184 | the private render state (17-21 votes each), index buffer 0x3144, targets, streams, textures, viewport 0x3218, scissor 0x3234, shaders 0x3244 / 0x3248, predication 0x3254, tiling |
| 13184 .. 13351 | +192 | clear colour / Z / stencil 0x3440 / 0x3450 / 0x3454 (bangaio-nx), InKickOff 13408 |
| 13352, 13360 | +216, +220 | KickOff / KickOffSegment |
| 13428 .. 13447 | +224 | VerticesRingEnd 0x3554 (EndIndexedVertices reads 13652) |
| 13480 .. 13491 | +232 | the export words 0x3590-0x3598 (bangaio-nx: BeginExport reads 13716) |
| 13492 .. 16516 | +236 | command buffer 13728, present interval 0x35F0, auto surfaces 0x3ABC-0x3AC4 (bangaio-nx: the front buffer `stw r3,15040`), critical sections 15156 / 15184, gamma ramp 0x3B70 |
| 16517 .. 21511 | +240 | SwapCount 0x4188, 16924, side buffer 16944, 21748 |
| 21512 .. 21564 | +244 | display mode 0x5500-0x550C, the -1 words 21776 / 21780, perf frequency 21804 |
| 21590 .. 21639 | +248 | 21840 / 21844 (Swap) |
| 21640 .. 22259 | +1928 | the title's -1 words 23600, 0x5E6C / 0x5E70 |
| 22260 .. 22271 | +1936 | BehaviorFlags 24200, flags2 0x5E88 |
| device size 0x5700 | 0x5F00 | Direct3D_CreateDevice `sub_8220E8A8`: `li r3,24320; li r4,128` |

Every value the zones give for a field bangaio-nx's tree names equals bangaio-nx's (its own measurement of Bangai-O's
device: `tools/d3d_device_layout.py`), so ilomilo's device is Bangai-O's. The snapshot is 0x3258 bytes (its last
64-byte chunk 24 bytes, which port 196's TakeLastChunk takes); the delta chain's private unread words 10880-11903;
the field classes' boundaries bangaio-nx's (unread to 0x2EAC, private to 0x2FB0, tail to 0x3234); kStateTagChunks'
private render state 0x2EAC + 0x104.

**Guest data** (`tools/d3d_data_addrs_ilomilo.py`: the address constants of the 5,613 paired functions, Bangai-O's as
bangaio-nx found them; constants compared byte for byte):

| What | Katamari | ilomilo | Evidence |
|---|---|---|---|
| XDK build qword | 0x82AD93F8 | 0x824B4A48 | 1 vote, the same bytes as Bangai-O's |
| VdGlobalDevice import slot | 0x82000750 | 0x8200072C | 17 / 17 votes |
| D3DCAPS9 | 0x820FC1F8 | 0x8201A930 | the same 304 bytes |
| full viewport | 0x820FAEB4 | 0x8201A010 | the same 24 bytes |
| XPhysicalAlloc no-large-pages flag | 0x8315DFE0 | 0x826C3500 | 2 / 2 |
| format table | 0x820FA9D0 | 0x8201A0E0 | 13 / 13, the same 128 bytes |
| HiZ owner | 0x8315E830 | 0x826C1860 | 3 / 3 |
| render / sampler state tables | 0x82AD8E48 / 0x82AD9308 | 0x824B4440 / 0x824B4900 | the default columns |
| export switches (NaN vertex, 512 pixels) | none (0) | 0x826C1870 / 0x826C1874 | 1 / 1 each (Bangai-O 0x8250C1B4 / B8) |

## First runs on the PC (2026-11-25)

- The PC build needed what git leaves out of a fresh copy of the base: the DXC binaries
  (`app/thirdparty/reblue-XenosRecomp/thirdparty/dxc-bin/bin` and `lib`), glslangValidator (`out/glslang`) and the
  deko3d host tools (`out/deko3d_tools`), all copied from the base's working tree; and the shader dump made before the
  first configure (`tools/renut_shader_dump.py`; Renut's CMake adds its own dump step only when the folder is
  missing, and that step's `app/tools/dump_shaders.py` is not in the base). Two Katamari functions the renderer calls
  by address (GetCurrentThreadId, D3D's XMemFree) did not link: ilomilo's `sub_822748B8` (the same three
  instructions) and `sub_82276218` (Bangai-O's XMemFree's pair). One layout assert: the delta chain reads 40 chunks
  here (Katamari 39, bangaio-nx's XDK 20209 40).
- The PC's Renut back end defaults to D3D12 (`renut_gpu_backend`); the runs take `--renut_gpu_backend=vulkan`.
  `--license_mask=1` (the full game, not the XBLA trial).
- `renut1` / `renut2` (Renut, 75 s): boot to the title screen with no crash and no missing shader, 60 fps by vsync,
  about 41 draws a frame; the generated-code self-checks, the r1 mirror and the stack forwards 0 differences. But only
  the top 256 lines of the picture are drawn; the rest is black.
- **Predicated tiling.** A RenderDoc capture (`out/rdc/title1.rdc`, `rdc_passes.py`, `rdc_draws.py`): the scene's
  colour and depth targets are 1280x256 (viewport 1280x720, scissor 1280x256). Renut's surface header is the XDK's own
  logic, so that is what the game asks for: 1280 x 256 x 4 samples x 8 bytes is exactly the 10 MiB of EDRAM, so ilomilo
  draws its 720 lines with **4x MSAA in three predicated tiles**. Its BeginTiling `sub_82215D10` and EndTiling
  `sub_82216378` (XDK 2.0.20209's shapes, which no reference port links: found by the device fields they write,
  TileCount +12924, the rects +12928, the extents +13356 / +13360, Flags +13364) read Katamari's registers exactly;
  the base's raw hooks (`BeginTilingImpl`, `EndTilingImpl`) are bound there. The game calls BeginTiling from four
  places (0x821F0D88 ...) and EndTiling from two.
- **After moving or adding a hook, post_codegen in full** (the base's xdk-notes): the first build with the tiling
  hooks still drew 256 lines, because `tools/direct_calls.py` had turned the game's calls of the then-unhooked
  `sub_82215D10` / `sub_82216378` into direct `__imp__` calls that skip the hook (`direct_calls.py --check` does not
  see this: it counts only calls still to convert). Check with a grep for `__imp__sub_<hooked address>(` in
  app/generated.

## Stale mentions (2026-11-25; optimising-functions.md, "What to do next" 3)

The copy tool's `Hooks` reads every source under `app/src` (and the SDK's): an address any of them names is never
copied. Of ilomilo's function starts, 340 are named there, nearly all by the Direct3D hook files themselves (hooked,
so not copies anyway: state.cpp 250, resource.cpp 39, device.cpp 27, draw.cpp 16, shader.cpp 5). The stale ones (a
comment naming another game's address that happens to be an ilomilo function start) are about seven, in
d3d_native_state.cpp, queued.cpp, d3d.h, render/draw.cpp, render/format.h and widescreen.cpp: negligible.

## Movies (2026-11-25)

ilomilo has one movie, `Data\media\upsell.wmv` (35 MB, WMV). The image names it next to the trial's screens
(`game:\data\media\upsell.wmv` at 0x82004798 among `TrialSelect`, `Upsell`, `IngameTrial`, `UpsellMenuPage`): the
XBLA trial's buy screen. The full game (`license_mask = 1`) does not play it. The WMV codec the base's Katamari hook
replaces (app/src/cpu/katamari_wmv_ffmpeg.cpp, vivapinata-nx's method) is in ilomilo at the same spacing, function
for function (`tools/d3d_best_match.py` against Katamari's image): status `823909F0`, GetData `82390AD0`, flush
`82390D90` (1.000), destroy `82390DE8` (0.909), decode `82390E98`, get output `82390EF8`; the stream node's payload
fetch is less sure (`823678C0`, 0.593). Not ported: nothing in the full game reaches it. Its file need not be in a
player's package (the installer can leave it out).

## Gameplay on the PC (2026-11-25)

- `play1` (the diet build, Renut on Vulkan, 150 s, `--input_script` 15:START, A presses every 5 s to 100 s, the sticks
  wandering from 110 s): the SouthEnd logo, the main menu (single player, multiplayer, gallery, leaderboards,
  achievements, help & options, download content, exit), "select a story", the prologue's level card, the loading
  screen with a tip, then the first level (from about 60 s), the sticks walking the character over the cubes. The whole
  720 lines draw (the tiling hooks); 60 fps by vsync, about 157 draws a frame in gameplay; every self-check 0
  differences (generated-code checks, r1 mirror, stack forwards, flush-mode flow); the DLC's sound bank (`dlc1.xwb`)
  loads. No unregistered function, no missing shader, no crash.
- Warnings: the game opens optional loose animation files (`animations\fx\*.pan` / `.trg`) that exist neither loose nor in
  the archives (the Xbox's open fails the same way); `XamVoiceSetMicArrayIdleUsers` is a stub; slow first reads of the
  wave banks on this PC.
- Renderer census (porting-guide-renderer.md section 2): **100 % immediate draws** ("draw sources: 94,181 immediate, 0
  replayed" per 10 s): no recorded command buffers, so the record-time items (setter marks, record-time objects, replay
  stream) have nothing to act on; the per-draw fast path, whole-buffer copies, mesh objects and the chain's reuse do.
  Each draw takes a whole device copy (1,157 MB per 10 s on the PC: the snapshot is 12,888 bytes).

## CG-13's census (2026-11-25, `tools/cg13_census.ps1 -Seconds 300`, the gameplay script)

`out/pc_runs/cg13_1`: 29 windows of 10 s, about 10,700-13,600 flush-mode switches a second in the game code (each an
`msr fpcr` the Switch build leaves out). 20 windows met denormals, at most 196 regions and 3 any-mode cold paths a second.
The sites (`tools/census_sites.py --denormal`):
- `banjo::FormsSelfCheck` (73 % of the counts): its own deliberate denormals at start-up.
- VMX code (`vmulfp128` in `sub_8222C910`, `sub_823178A0`, `sub_8222C6B0`; `vaddfp128` in `sub_8229FA38`; `vsubfp128`
  in `sub_82258ED8`, `sub_822A5110`): the Xenon's VMX flushes denormals itself, so the one flush mode gives the same
  results there.
- `sub_822584E8` (36 counts in 300 s): `lfs` / `stfs` copies of single floats into a stack block that it then loads
  with `lvx` into VMX math (16-bit vertex data written to r17 beside it): a denormal flushed by the copy would be flushed
  by the VMX on the Xenon anyway. Same result.
- `sub_821B31C8` (2 counts): a setter storing its float arguments into an object (`stfs f1,4(r3); stfs f2,8(r3)`, f3 /
  f4 by flags), called from the game's code around 0x82112xxx: twice a value below FLT_MIN that the Switch build stores
  as 0. A value decaying to zero; no division or guard by it was seen.

**Verdict: keep `BLUR_FPCR_ONE_MODE` ON for the Switch (the base's default).** Run it again after a large change to the
code generation, and in the later levels (the DLC's) once a script reaches them.

## Hot functions: the machine track, first batch (2026-11-25)

The PC profile (`prof1`: `banjo_pc_profile_s = 60`, 240 s: menus, the story intro and the first level;
`out/pc_runs/prof1/pc_profile.log`, `tools/pc_hot_functions.py --guest`): guest code is a small share of the PC's
busy samples. The main thread runs about a quarter of a core (`sub_820CE3E8` 5 %, `sub_82436070` 4 %, `sub_821D04F0`
2.4 % of it); two worker threads (XThread9CA0 / 8E04) sit in `sub_821EE700` (11-13 % each: a wait loop, most likely);
another worker in `sub_8229FE20` (3.8 %); the Audio Worker in `sub_8229C2D8`.

Every sampled guest function (163) goes on the bulk list (`app/src/cpu/hot/localized_bulk.txt`), less the tiny leaves (5,
12 instructions or fewer) and those under 40 instructions with fewer than 50 samples (15; idea 30): **94 functions**.
Hand-written natives: none (they need console profile data past the gate).

- One more rule for a hand-made list: localize_native.py does not check a list's own entries against the app's hooks,
  so Renut's hooked `sub_8220F0A8` (GetMipTailLevelOffsetCoords) linked twice ("duplicate symbol"); dropped with the
  tool's own `Hooks([]).replaced()` filter. **90 copies** (three refused by the tool: `sub_82299C78` and
  `sub_82298D58` read the time base, `sub_82282760` has MMIO-capable loads).
- **Guard on the PC** (`guard1`: tools/run_pc_verify.ps1, `banjo_cpu_verify`, `banjo_hot_guard_calls = 4000`,
  `banjo_hot_guard_period = 1`, 240 s through the menus into the first level): **90 of 90 copies reached, 95.2 million
  calls compared, 0 differences** (8.9 million not comparable: stopped in both forms with the same stores before a
  real call; one differed once and not when repeated: another thread changed its inputs). Generated-code checks,
  r1 mirror, stack forwards, flush-mode flow: 0 differences.

## The Switch build (2026-11-25)

- Shader package (`tools/switch_shaders.ps1`, run during another session's build: single-threaded tools): all 218
  shaders through Renut's XenosRecomp, the early-alpha pass, SPIR-V -> GLSL, the base's 48 GLSL passes and uam: 218
  compiled, 0 failed (140 vertex DKSH, median 15 KB, largest 266 KB; 78 pixel, median 3 KB); the GLSL package 11 MB ->
  979 KB (`app/out/renut_switch/deko3d_glsl.bin`), the Switch shader cache 51 KB + 1,016 KB of SPIR-V.
- `tools/build_switch.bat` (app/out/switch, devkitA64, deko3d only: NVK not linked; the machine copies in place;
  `BLUR_FPCR_ONE_MODE` ON): 1,041 steps in about 30 minutes; `renut.nro` 43.0 MB.

## The first emulator runs (2026-11-25)

- `emu1` (Ryujinx, 330 s): the NRO ran (it wrote its VFS index, installed the DLC, compiled pipelines into
  `pipeline_list.bin` / `deko3d_shaders.bin`), but no log and no capture came back: the test toml was not applied. It
  had keys twice (`log_level`, `banjo_stall_watch_seconds`, appended to a file that had them), and TOML refuses a
  duplicate key, so the whole file was dropped and the built-in settings (no log) ran. Also found then: files written
  with Windows PowerShell's `Set-Content -Encoding utf8` carry a UTF-8 BOM (Python's tomllib refuses it at line 1); the
  built-in settings file had one (stripped; toml++ skips a BOM, so the NRO read it). `tools/make_emu_toml.py` now makes
  the test tomls with the keys set in place and checks them with tomllib first.
- `emu2` (Ryujinx, 330 s, `out/emu_tomls/emu_verify.toml`): the log came back. The game boots, installs the DLC,
  reads its archives and loads the title's models and textures, but the frames stop: the render thread ends 5 frames
  in the whole run ("GPU profile ... over 5 frames"), the game thread's 10 s report (built at each Swap,
  `StatsGameFrame`) never appears, and every capture finds no picture. Draws keep coming all the same: per "frame",
  1,628 of the depth-of-field composite (0B4973CE2EEC601A, one a game frame on the PC) and 89,518 of the scene's
  main shader, so about 8,100 whole game frames were drawn that never reached Renut's Swap. With no frame end the
  command memory is never recycled: 1.5 GB of deko3d blocks, four "long frame splits", and Ryujinx's "GPU processing
  thread is too slow" / "WaitOnSyncpoint ... took more than 1000ms" follow from that. All three Swap call sites in the
  generated code call the hook (`sub_82215280`, linked from device.cpp in the Switch map; the game's present routine
  `sub_821F33E8` is generated code, not a machine copy). Next: a run with the stall watchdog on
  (`out/emu_tomls/emu_stall.toml`: `banjo_stall_watch_seconds = 5`, its wait lists) to see where the game thread is.
- `emu3` (Ryujinx, 200 s, the stall watchdog on). In Ryujinx the NRO's argv[0] has no folder, so the log folder of the
  crash and profiler logs (`RexSwitchLogDir`, logs/rex next to the NRO) is never set: the watchdog writes
  `banjo_profiler.log` to the process's working folder, the emulator SD's `/switch/`, and its on-demand trigger is
  `sdmc:/switch/stall_dump` (its first line says so; `tools/ryujinx_stall_dumps.ps1` wrote it in the wrong place). Its
  dumps (named with `tools/switch-cpu-profile.py`, devkitA64's nm on PATH; `out/emu_runs/emu3/profiler_named.txt`):
  2 frames so far; the guest **main** thread is not blocked: 1.8-2.0 s of CPU in each 2 s, in the game loop and
  drawing: `xstart` -> sub_82110040 -> sub_820EFDC8 -> sub_821CE4F8 -> sub_821AB3C8 -> sub_82193768 -> sub_821F15B8
  (a call through slot 0x44 of the global object at 0x826ACC58) -> the in-place copy of sub_820F3040 -> sub_820C85E0
  -> the copy of sub_820C6010 -> sub_82204560 ... -> the DrawPrimitive hook -> QueueDraw. Several bulk machine copies
  are on that path (sub_820F3040, sub_820C6010, sub_82198448, sub_820B9270, sub_821D04F0, sub_8218BB58), and the PC
  ran the same 90 copies (hooked, guarded: guard1, 60 fps) where the Switch runs them in place: the copies are the
  first suspect. Test: every bulk entry marked `off` (the original list kept in `out/localized_bulk_all_on.txt`), only
  the copy shards and the link rebuilt; then a bisect if the frames come back.
- `emu4` (every bulk copy `off`; post_codegen with `tools/keep_mtimes.py` around it: 328 generated files unchanged
  and given their old times back, only the 12 shards rebuilt, a 2-minute build): the same stall (2 frames). **The
  copies are not the cause**; the list is back to all 90 (the shards stay `off` until the next post_codegen).
- `emu6` (`ilomilo_frame_diag`, app/src/cpu/ilomilo_frame_diag.cpp, a key, off by default: counts ilomilo's render
  routine sub_821F15B8 and present routine sub_821F33E8, logs guest words every 2 s from a pthread; `emu5` ended in
  `std::terminate` because `std::thread` throws "Function not implemented" on the Switch): the game loop runs about
  500 frames a second (its frame time advances in real time, the render routine is called each frame), the present
  routine has run twice, and the render device pointer [0x82645070] is set. The game renders and then chooses not to
  present. The reason, from the code: the scene render (sub_820F3040) ends with `if (!device->slot_0xFC())
  device->slot_0x108()`; slot 0xFC (sub_821F3168) returns the render device's **suspended flag** [0x826B71FC], which
  its Suspend (slot 0xF4, sub_821F3098: D3D's device suspend sub_8220E458, then 1) sets and its Resume (slot 0xF8,
  sub_821F3100: sub_8220E4F0, then 0) clears. So after two frames something suspends the render device and never
  resumes it in the emulator. Candidates: the routine sub_82365B50 (it suspends and resumes guest threads, takes the
  device's thread ownership and presents through D3DDevice_Present itself) and its module (0x82363xxx-0x82365xxx:
  sub_823655D8, sub_82363308, sub_82363150 call slot 0xF4); Ryujinx refused its thread suspend and resume
  (`SetThreadActivity() = InvalidHandle`, logged at the scripted presses). Next: the diagnostic logs each Suspend /
  Resume with its caller and sub_82365B50's entry and exit (built, waiting for a slot).
- `emu7`: one device Suspend, at 16.7 s on the main thread (the one that made the D3D device and registers the
  notification listeners), never a Resume; sub_82365B50 never runs (the guest LR reads 0 here: the diet elides the LR
  saves, so the next diagnostic takes the host stack with `_Unwind_Backtrace`). The code that does it is the scene
  render's state 0 (the start-up logo; sub_820F3040 at 0x820F31A4, the object at [0x826ACC58], its state at +16):
  each frame it first resumes the device once `TickCount - [state+40] > 1000` (TickCount: KeTimeStampBundle's, the
  import at 0x820005E4, +16, read by sub_8218FBE8; [state+40]: the TickCount at the state's entry, sub_820F5358), then
  draws the logo unless suspended, and on its 2nd frame presents and suspends (0x820F3300: the logo held on screen
  for a second while loading goes on). So in the emulator the tick count never gets 1000 past the stamp. The SDK
  refreshes it from `Clock::QueryGuestUptimeMillis()` with a repeating timer (`kernel_timestamp_interval_ms`; the
  emulator's rex_profile shows the timer firing about 100 times a second). Next run: the diagnostic logs the
  TickCount, the state and the stamp every 2 s.
- `emu8` (the TickCount, the scene's state and stamp every 2 s): the TickCount advances normally (6,759 -> 28,829 over
  44 s); state 0's stamp is 4,764; at the first report (2 s) the scene is still in state 0 with 2,000 ms gone, but
  only 4 renders had run (the first frames compile their pipelines), and by the next report the game's update had
  moved the scene to state 5 (later 2). Only state 0 resumes, so the hold never ended. **Cause: the logo's hold
  relies on a state-0 frame running after its second has passed; with slow first frames none does.** The PC renders
  60 a second from the start, so its state 0 resumes it.
- **The fix, `ilomilo_logo_hold_resume` (on; app/src/cpu/ilomilo_frame_diag.cpp):** the hooks on the render
  device's Suspend / Resume (slots 0xF4 / 0xF8, reached only through the vtable, so no post_codegen is needed) note a
  Suspend made in state 0; when the scene's state is no longer 0 at the next frame's render (slot 0x44, sub_821F15B8,
  r3 the device) and the device is still suspended by it, the device's own Resume runs there. At normal frame rates
  the game resumes first and the fix does nothing. `emu9` (Ryujinx, 200 s): the fix acted once (state 1), and the
  game ran at 55-60 fps from then on: the SouthEnd logo, the title and story select, a loading screen, the prologue
  card and the first level in the 12 captures (`out/emu_runs/emu9/sheet.png`).
- **A Switch-only picture fault, being chased:** large areas of a solid colour (blue, red or green, changing between
  screens) where the PC shows the pale backdrop: the top two of the three 256-line tiles. That colour is the game's
  own clear colour for those tiles (BeginTiling's pClearColor, kept at device +0x3440, which BeginTiling's own code
  confirms: `stvx128` there, zeros when none), normally covered by the backdrop. First suspect: the deko3d-only
  colour hand-over (`banjo_deko3d_color_handover`: a whole colour resolve not drawn, the texture sampled from the
  target's image), which reports 2 resolves a frame not drawn while ilomilo resolves its tiles one by one and clears
  the target after each. Test: the same run with the hand-overs off (`out/emu_tomls/emu_ho_*.toml`).
  - emu10 (colour hand-over off), emu11 (all four hand-overs off), emu12 (`banjo_noncpu_enhancements = false`: every
    non-CPU enhancement off) and emu13 (the deko3d depth items off: 24-bit depth, precise depth resolve, the float
    depth-resolve shader): the same colours in every one. Not an optional item: the core deko3d path, or Ryujinx.
  - Re-read: the colours are expected in the target before the backdrop draws (tiles 0-1 are prepared with
    BeginTiling's colour, tile 2 with EndTiling's, as the original EndTiling does for the next tile), and the PC's
    backdrop covers them every frame. The emulator's per-shader GPU profile at the title adds up to the PC's ~105
    draws a frame, so the backdrop draws are issued; what they write does not show. The texture formats are mapped
    alike by both back ends at Renut's level (DXT1 55, 8 50, DXT4_5 61, 8_8_8_8 20). Next: a RenderDoc capture of
    Ryujinx at the title (tools/run_ryujinx_rdc.ps1, now pointed at this port's folders) and a pixel history
    (tools/rdc_pixel.py) at a blue pixel.
  - **RenderDoc (out/emu_runs/rdc_emu1, frame 841, the title menu; out/rdc/emu1*):** pass 0 (56 draws into the
    1280x720 colour target 1808) renders the 3D title scene correctly. The depth-of-field chain follows: a depth
    resolve per tile (into R32F 1987), the scene's tiles resolved into 2394, then **draws of 24 vertices: a rectangle
    list of 8 full-height strips 0.25 wide** (2394 + depth -> 2406, 2406 -> 2446, 2446 + depth -> 2406, 2406 ->
    1808), and the menu (pass 9). The slanted wedges start at the first of them (event 664). Its geometry stage
    (Renut's rectangle_list_gs, in Ryujinx's translation) is right: 48 vertices out, each fourth corner and its
    texture coordinate correct (tools/rdc_mesh_gs.py, rdc_gsout_attrs.py). The pixel history of 2406 at event 664
    (rdc_pixel.py): fragments `depthClipped`, one `shaderDiscarded`. The rectangles lie exactly on the far plane
    (z = w = 1), where Renut's pipelines clip (`depthClipEnabled` always); with rounding some fragments fall past it
    in the emulator, keep the last frame's pixels, and after the tile resolves and clears the composite shows the
    clear colours. The PC driver keeps z = w.
  - **Change (built next):** `ilomilo_renut_clip_disable` (on): a draw whose PA_CL_CLIP_CNTL has clip_disable (bit
    16) gets a pipeline that clamps depth instead of clipping it, as the Xenos does not clip it (render/draw.cpp
    MakeKey sets mode_control bit 3, render/pipeline.cpp `depthClipEnabled = !(bit 3)`); the first rectangle-list
    clip controls are logged ("[ilomilo] a rectangle list with PA_CL_CLIP_CNTL ..."). If ilomilo leaves clipping on
    for these passes, the fault is Ryujinx's rounding at the far plane and the console is expected to be clean (to
    be checked there).
  - emu16: ilomilo's rectangle lists come with PA_CL_CLIP_CNTL `00080000` (D3D clip space, clipping on), so the
    clip_disable key does not act; the picture is unchanged. `ilomilo_renut_rect_depth_clamp` (on; rectangle lists
    clamp depth, the same pixels for any rectangle inside the depth range) built for emu17: unchanged as well. Ryujinx
    turns host depth clamping on whenever the guest's ViewVolumeClipControl lacks DepthClampDisabled (its
    StateUpdater.UpdateDepthClampState), so the clamp did reach it: the "depthClipped" flags may not be the cause.
    Next: a capture of this build, the blur draw's pixel history again, and its pixel shader (the one
    `shaderDiscarded` fragment: the depth-of-field shader may discard by the depth it samples).
  - More of the capture: across the first rectangle, some pixels have no fragment of the blur draws at all and
    the others are `sampleMasked` (some also `shaderDiscarded`: its alpha test). The same draw had the shadow pass's
    depth bias (13422 / slope 2.0) bound; but emu18 (`rr6_depth_bias = false`) and emu19
    (`sasrt_rt3_depth_bias_fields = false`) show the same wedges, so the bias is not it either. emu20
    (`banjo_renut_fast_draw = false`, `blur_renut_provisional_key_kept = false`: 0 fast draws, 9,745 full, every
    pipeline built for its own key) shows the same wedges as well: neither the fast path nor the reuse of a
    provisional pipeline is the cause.
  - **Where it stands:** the rectangle list's geometry stage emits the right rectangles (RenderDoc's post-geometry
    data), the PC's Vulkan path draws the same passes correctly with the same geometry shader, and the deko3d pipeline
    binds the geometry stage; in Ryujinx the rectangles' second halves are not rasterised. This points at Ryujinx's
    handling of this geometry-shader path, not at the port; **the console has to decide** (the user's next step:
    the title screen's backdrop and the levels' pale sky must be whole). The two keys tried here stay in the build
    **off** (`ilomilo_renut_clip_disable`: the Xenos' clip_disable honoured with depth clamping;
    `ilomilo_renut_rect_depth_clamp`: rectangle lists clamped), since neither changed the emulator's picture.
  - A PC reference capture (tools/run_pc_rdc.ps1) was tried twice and gave no capture (the app's own trigger said
    FAILED; qrenderdoc's trigger fired but no file came): left for later.
  - **The cause (tools/rdc_ms.py on the same capture, 06:00):** the blur draw's multisample state is plain (1 sample,
    mask all ones, no alpha to coverage), but Ryujinx's translation of Renut's rectangle geometry shader declares
    `gl_ClipDistance[8]` and writes element 0 before every `EmitVertex` from **`gl_in[i].gl_ClipDistance[0]`, which
    the vertex shader never writes**: under `sasrt_gpu_clip_spec` a draw with no user clip plane gets its vertex
    shader with constant 929 = 0 (no clip distance), while rectangle_list_gs.hlsl (and point_sprite_gs.hlsl) still
    pass `SV_ClipDistance0` through. On the console plume turns the clip slot off for such a pipeline (noUserClip,
    plume_deko3d.cpp createGraphicsPipeline: constant 929 = 0), so the hardware ignores that output; Ryujinx clips
    with whatever the last stage writes (the base's own note on `banjo_deko3d_user_clip_enable`), so each rectangle
    is cut on an undefined value. That explains the wedges (whole or partial triangles), RenderDoc's "clipped" flags,
    and why none of the depth, bias, hand-over or fast-path keys mattered. **Expected clean on the console** as it is.
  - **Fix: `ilomilo_renut_gs_no_clip` (on).** rectangle_list_noclip_gs.hlsl and point_sprite_noclip_gs.hlsl (the
    same shaders with `RENUT_GS_NO_CLIP`: an output vertex without the clip distance; built by gpu.cmake's
    renut_host_shader, which now takes the included file as a dependency), used by render/pipeline.cpp Build when
    the key's reserved bit 3 is clear (exactly the draws whose vertex shader gets 929 = 0). The usual shaders are
    unchanged (the deko3d blob is byte-identical: 302,517 bytes). Console: the clip slot was off for those draws
    already, so the same pixels, and a few outputs fewer a vertex. Ryujinx: no undefined clip distance. Test plan:
    emu21 with `sasrt_gpu_clip_spec = false` on the current NRO (the vertex shader writes a 0 distance again: the
    wedges should go, confirming the cause), then the build with the fix and emu22 with the normal toml.
  - emu21 (`sasrt_gpu_clip_spec (off) 0` in its log): still coloured areas, but **of another shape**: whole
    rectangular strips missing instead of diagonal halves, so the clip value does decide what is lost. A 0 in slot 0
    is not enough because Ryujinx's GS also declares clip distances 1-3 (its epilogue writes elements 1-3 after the
    last `EmitVertex`, so the emitted vertices carry undefined values there: uam's GS output covers the clip
    distances as one group of four). Only a GS that writes no clip distance at all leaves Ryujinx none to clip with:
    the fix's variant. emu22 (the build with the fix) decides.
  - **emu22 (build a2bf63ec + this fix and 32 more copies, built-in settings, 120 s): fixed.** The Southend logo,
    the title menu with its backdrop, the loading card and the first level with its pale sky are whole in every
    capture (out/emu_runs/emu22_sheet.png); 56-60 fps; no error beyond the 894 `ResolvePath ... device not found`
    lines every run has (the game probing device paths). The Switch-only picture fault was Ryujinx clipping on the
    geometry shader's undefined clip distance; the console was expected clean before and is unchanged by the fix.
    The PC is unchanged too: constant 929 exists only in the deko3d GLSL (tools/deko3d_glsl_opt.py pass clipspec),
    so the PC's vertex shaders still write their distance, 0 for a draw without a plane (clips nothing); the no-clip
    GS writes none (clips nothing either), and a draw with a plane keeps the usual GS (key bit 3 set).
    Handoff 6 for the base (D:\ilomilo\out).

## SMAA (2026-11-25)

The final composite: `banjo_renut_diag_draw_log_s = 125` in gameplay (the CG-13 run, two frames of 161 draws): the
scene into the 1280x720 target, a clear, two full-screen rect-list passes into a second target (the depth-of-field
blur: pixel shaders `5D2224AD595D5FCC`, `949ED45F4495B293`), then **`0B4973CE2EEC601A`**, a full-screen pass back into
the main target (the depth-of-field composite), then the HUD (alpha-blended strips and quads). The same in both frames.
`banjo_renut_smaa_after_ps = "0B4973CE2EEC601A"` (built-in settings and the package tomls): the PC's 10 s line then
says "SMAA ... 600 frames" in gameplay. (Menus that draw no depth of field get no SMAA.)

## Eligible batch 1 (2026-11-25, the base's optimising-functions.md "What to do next" 1-2)

- **The choice** (tools/hot_eligible_batch.py, new): every generated function by tools/switch_hot_bulk.py's own rules
  (no tiny leaves, nothing under 40 instructions, nothing an app or SDK source mentions, no threaded dispatch,
  localize_native.fits()): **5,222 eligible of 12,597**. The direct callees of the copies first (none eligible:
  already copied, tiny, small or not generated code), then their callers (a function that calls a hot one tends to run
  often itself): **500 taken**, the list now 636 lines (633 copies made, 3 refused as before).
- **Cost:** post_codegen 16 minutes (105 generated files changed, 1,000 new files of the copies); the everyday
  Switch build 8 minutes (92 steps); **NRO 45.8 -> 49.0 MB: about 6.4 KB a copy** (the base guessed 11 KB). At that
  rate all 5,222 would add about 33 MB. D: had 30 GB free afterwards.
- **verify3** (the PC build with batch 1, 240 s, the gameplay script): 346 of 633 copies reached, 123.4 million calls
  compared, **one difference**: `sub_820B3F90`, **not a batch-1 copy** but one of the first 90 (prof1, 554 samples, a
  3x4 matrix product: loads from r4 and r5, 12 stores at r3; a leaf, its copy unchanged since 07:18 and matching every
  call in guard1 and verify2): "f1 copy=0xc045a27d60000000 original=0x0000000000000000 (3 passes in a row); inputs
  r3=0x7010f230 r4=0x42911150 r5=0x42911380 r6=0 r7=0 f1=0x3f90c50000000000 f2=0x3feffe1980000000; 52 bytes in 2 written
  ranges", after 61,854 calls compared; the guard switched it off for the rest of the run. Both forms compute f1 the
  same way (`fmadds f1,f26,f22,f6`, the same loads and store order), so the cause is not visible in the text: an input
  this run reached for the first time (r3 is a stack address; the 52 bytes include the LR save at r1-8). Not chased
  further today. **Taken out** of the list with a `# out:` line (the base's rule for a copy the guard rejects); rc1's
  NRO still has it in place, so rc2 replaces rc1. Then post_codegen, the Switch and PC builds and verify4 again.
- **verify4** (632 copies, the same script, 240 s): 345 of 632 reached, **115.9 million calls compared, 0
  differences** (one call differed once and not when repeated: another thread changed its inputs); generated-code
  self-checks, r1 mirror, stack forwards: 0 differences. The 287 copies no run reached are unchecked (the base's
  caveat: "a check that never ran proves nothing").
- **Ryujinx, batch 1 in place:** emu29 and emu30 ran while the machine carried the SEGA session's 6,745-shader
  translation and two PC runs: Ryujinx took ~88 s just to start the 49 MB NRO (its own log), so emu29 reached only
  the title (its log's tail was also lost: my output filter stopped the runner before it collected the logs; the
  SD's toml was put back by hand: there was none before the run) and emu30 wrote no game log at all. Neither says
  anything about the copies; to be run again on a quieter machine. (The load turned out to be five orphaned uam.exe
  of the SEGA session's crashed shader step, ~40-45 GB of commit memory from 10:36; that session stopped them at
  ~11:10, which also let a third run, refused at 11:05 with 7.7 GB free, start.)
- **emu31_rc2** (the release NRO with the 632 copies in place, deko3d_glsl.bin beside it, the player's default
  ilomilo.toml only, the master game folder, 240 s on a quiet machine: 44 GB free): the logos, the title, "select a
  story", the loading card and the first level played through several of its areas (20 captures); 48-60 fps in the
  10 s reports; no error beyond the usual ResolvePath lines; no crash. With verify4 on the PC, batch 1 goes into rc2.

- **Eligible batch 2** (500 more callers of the copies; the list 1,135 lines, 1,132 copies): post_codegen ~25 min,
  the everyday Switch NRO 49.0 -> 51.1 MB. **verify5** (PC, 240 s, the gameplay script): 565 of 1,132 reached, 75.4
  million calls compared, **0 differences**.
- **rc3** (the release NRO with the 1,132 copies in place: 49.1 MB). emu32_rc3 (Ryujinx, the player's default
  ilomilo.toml, the master game folder, 240 s, a quiet machine): the full game's menus, the prologue map, the loading
  card and the first level through several areas (19 captures); 59-60 fps; no error beyond ResolvePath; no crash.
  The user asked for rc3 as a console build with profiling on in the toml: dist/switch/ilomilo_profiling.toml (the
  player's options plus switch_profile_stacks, banjo_cpu_profiler and the log) is its ilomilo.toml.
- **Why the NRO grew although the copies are in place** (the user asked; rc1 against rc2's ELF, aarch64 nm/size):
  `.text` 32.86 -> 35.63 MB. The 500 batch-1 functions themselves shrank (1.83 MB generated -> 1.21 MB as copies in
  place: the originals are dropped, as the user expected). The growth is 179 copies emitted a second time as
  `banjo::hot::n_X::f_sub_X<Fast>(...).isra.0` (2.81 MB): the body other copies call directly (copy-to-copy calls
  skip the hook), which the compiler kept out of line beside the in-place `sub_X` that inlines the same body. Batch 1
  was chosen as callers of copies, so it has many such direct calls. Making the in-place `sub_X` and the direct-call
  body one function would take most of that back: a copy-tool change for the base (not done here).
  **The user (2026-11-25, 11:55): the growth is fine ("things just inlined, which is a good thing"): no change.**

## Late input (2026-11-25)

`banjo_late_input = true` (built in, and in every toml). It acts on the Switch build: emu22's `[latency]` lines (the
first level, every 10 s): "late input: the first controller read of a frame delayed 5.4 ms on average (601 frames)",
input -> swap 1.0 ms. These are an emulator's timings, so they are not compared with anything; the console's log has
the same line.

## Smaller game files: Opus, H.265, LZ4 / ZXC (2026-11-25, the user's request via the Ridge Racer 6 session)

The user: "re-encode their audio and video to opus and h265 and L4Z/ZXC stuff as a part of the progress". The method
is the base's docs/media-compression.md; the base's SDK already reads every stand-in used here (port 259: `.lz4b`
versions 1-2, `.xmop`, `.opcm`; 22,050 Hz `.xmop` sounds since port 278), so only the movie needs code in the NRO.
Everything is made by the web installer (D:\ilomilo\ilomilo-nx-installer) from the player's own files; the PC tests
write under out/media and D:\ilomilo\game_media (game data: never committed).

- **What the game has** (D:\ilomilo\game, 224 MB): 9 XACT 3 wave banks (`Data/sound/Xbox/*.xwb`, version 46, header
  version 44; 80.5 MB): 435 XMA sounds, mono and stereo, each at its own measured rate (42,522-44,570 Hz), and PCM
  16-bit big-endian sounds (startup.xwb, 17.5 MB, is all PCM); one movie, `Data/media/upsell.wmv` (WMV3 1280x720 59.94
  fps 7 Mbit/s, WMA Pro stereo, 37.0 MB; the trial's buy screen only); 359 `.dds` textures (95 MB); 5 `.par`
  archives (ZIP, deflate: 16.9 MB); fonts (19.7 MB); small rest.
- **Audio, XMA -> `.xmop`.** The installer's reader for XACT 3 banks (`lib/xact3.js`, game.json audio container
  `xact`; after vivapinata-nx-installer's XACT 2 reader: the regions start at byte 12). The SDK only compares a
  sound's declared rate with its Opus rate (to resample), never with the stream's, so `near_hz` 1700 declares every
  ~44 kHz sound 44,100 Hz (48 kHz Opus, 160/147 back): the game's voice keeps its own rate. Music 128 / 64 kbit/s,
  the rest 96 / 48; ids `0x69 << 24 | bank << 16 | sound`. PC test (`test/xmop_node.mjs`, ffmpeg libopus): the 8 XMA
  banks 63.0 -> 53.0 MB; every file `test/xmop_check.mjs` OK (headers, frame lengths, last bits, tags, walks). The
  music barely shrinks (44.0 -> 41.8 MB): its XMA is already ~134 kbit/s against Opus at 128. **The user's call:** the
  music at 96 / 48 kbit/s would save about 11 MB more (it changes what is heard).
- **Audio, PCM -> `.opcm`.** banjo-nx-installer's `lib/opcm.js` (its XACT bank finder) for startup.xwb (game.json
  `opcm`, a third media kind); its byte-order guess was wrong for one sound (entry 8, stereo 2.98 MB: steps 503
  big-endian against 21,826 little-endian, the guess divided by the levels said little): it now compares the raw
  steps (the guide's rule). 17.53 -> 1.85 MB, every non-PCM byte stored.
- **The movie, WMV3 -> H.265 in the ASF** (installer `movies`, fraction 0.35, gop 120, then ZXC). The NRO's hook:
  `app/src/cpu/ilomilo_wmv_ffmpeg.cpp`, the base's Katamari hook at ilomilo's addresses of the same XMedia WMV9
  wrapper (decode sub_82390E98, get output sub_82390EF8, flush sub_82390D90, destroy sub_82390DE8, GetData
  sub_82390AD0, status sub_823909F0; the interface filler sub_82391478 stores them at Katamari's offsets; reached
  only through that interface: no regeneration needed). PC test with culdcept-nx's `tools/hevc_movie.py` (NVENC):
  35.2 -> 13.4 MB (38.1 %, 2,519 frames). The full game never plays it (trial only). Built since the 05:29 NRO
  (Switch only: RENUT_NXVIDEO). Its Ryujinx test: trial mode (`license_mask = 0`), software H.265
  (`ilomilo_movie_nvdec = 0`: Ryujinx emulates no H.265 NVDEC), the SD's game_root on D:\ilomilo\game_media
  (tools/ryujinx_game_root.ps1), out/emu_tomls/emu_trial.toml.
  - emu23_trial (110 s, the media folder: the 8 `.xmop` banks, `startup.xwb.opcm`, the H.265 `upsell.wmv`): the trial
    boots and plays from the media folder (logo, title, the trial's main menu with "unlock full game", the trial map,
    a loading card, the tutorial level); the game folder link put back after. The default script picked "single
    player", so the upsell page was not reached: emu_upsell.toml goes down six times to "unlock full game" (43-48 s)
    and presses A (50 s), captures every 3 s. Its audio came from the stand-ins: the log's `[xmo]` lines load all 8
    banks' Opus sounds (music 20, ambience 50, narrator 77, misc 108 ...), and the 10 s reports show sound playing
    (426-464 of ~430-470 audout buffers non-zero, peak 0.12-0.22, nothing saturated).
  - emu24_upsell and emu25_upsell (the first overlapping Poker Smash's release build, under the user's new rule: two
    builds and one Ryujinx run at a time, a run may overlap builds): both ended on the trial map. Loaded, the
    intro is slower (logos 32-45 s, the door 45, the title 48, the menu 51), and the menus read the script's presses as
    queued key events: presses made while loading are consumed by later screens, and a left-over A chose "single
    player" before the DOWNs came. emu_upsell3.toml presses nothing until the intro is surely over: START at 70 s
    (the title), DOWN six times at 75-80 s, A at 83 s.
  - emu26_release (the release NRO, the media folder, trial, emu_upsell3.toml): the title says "press A to start" and
    ignored START, so it waited until about 88 s; the queued DOWNs then walked the menu (single player, gallery, help
    & options) and the log ends at script time 78 s (the script's clock starts at the first poll, ~17 s after boot):
    whether the upsell page opened is not recorded. **Stopped there on purpose:** the user asked (2026-11-25, 08:00)
    to make sure the game runs in non-trial mode, and the movie plays only in the trial. The hook stays built,
    untested; the full game never reaches it.

## The full game, not the trial (2026-11-25, the user: "Make sure the game runs in non trial modr")

- **The Switch NRO** has `license_mask = 1` built in (app/ilomilo_switch_defaults.toml, compiled in by
  KATAMARI_BUILTIN_CONFIG) and every shipped toml says so too (renut.toml, renut_play.toml, renut_ab.toml and the 8 in
  configs/: `license_mask = 1`); the player's ilomilo.toml (app/ilomilo_switch.toml) does not set it, so the built-in
  1 holds. The trial runs above set `license_mask = 0` in their own test tomls only.
- **Checked:** emu27_release_full, the release NRO (app/out/switch-release) with the player's default ilomilo.toml
  only and the master game folder: the full game's main menu ("download content", no "unlock full game"), "prologue
  / meet up", the loading card and the first level; `[deko3d] GLSL package: 218 shaders, 979 KB` read from
  deko3d_glsl.bin beside the NRO.
- **The PC** has no built-in config (its log: "No config file at ...\renut.toml: defaults"), and the SDK's own default
  is 0. Its runs showed the full game anyway (play1: "download content", "select a story", the prologue), but it is
  now explicit: tools/run_pc.ps1 passes `--license_mask=1` (`-License 0` for a trial test).

## Release candidate 1 (2026-11-25)

- **The NRO:** tools/ilomilo_build_switch_release.bat (new): app/out/switch-release, the everyday build's 70 options
  but `BANJO_RENUT_RELEASE_SHADERS=ON` (no game shader inside; tools/renut_release_shaders.py first), no PGO or LTO
  (they wait for the user). 13 minutes, 43.8 MB (the everyday one 45.8 MB).
- **The DKSH cache:** tools/deko3d_variant_cache.py on Ryujinx's pipeline list (out/pipeline_lists/ryujinx_0716.bin):
  1,326 pipelines, 293 variants, 0 failed, 965 KB (out/deko3d_shaders/deko3d_shaders.bin, in the package).
- **The machine copies, verified** (`verify2`: tools/run_pc_verify.ps1 -Seconds 240, the PC build with the 136-line
  list): 133 of 133 copies reached and on, **137.1 million calls compared, 0 differences** (20.5 million not
  comparable: stopped in both forms with the same stores before a real call); generated-code self-checks, r1 mirror,
  stack forwards, flush-mode flow: 0 differences. (Two Windows-only breaks in ilomilo_frame_diag.cpp fixed first:
  pthread.h and _Unwind_Backtrace.)
- **The guard build** (tools/ilomilo_build_switch_guard.bat, new wrapper: app/out/switch-guard, the copies hooked with
  their guard forms; 48.2 MB) **in Ryujinx** (`emu28_guard`, 240 s, `banjo_hot_guard_calls = 4000`, period 64,
  `banjo_cpu_verify`): 115 of 133 copies reached, **20.0 million calls compared, 0 differences**. With every call run
  twice it reached only the title in 240 s; the PC's verify2 covers the gameplay. `banjo_hot_poison_dead` was on too
  but never acted there: it poisons only after unguarded calls, and `banjo_cpu_verify` guards every one (its log
  line never came), so the poison check is its own run.
- **The poison check** (`poison1`: the PC's hooked build, `banjo_hot_poison_dead = true`, the default guard spacing,
  so nearly every call unguarded and poisoned after; 240 s, the full game, the gameplay script): the line
  "banjo_hot_poison_dead: the copies' dead-after-return registers get garbage from now on" at 08:52; 126 of 133 copies
  reached; 0 differences, no crash; the menu, the prologue and the first level played as before (captures). No copy's
  liveness claim (tools/reg_liveness.py, leaf_dead_stores.py) is wrong where the game went.
- **The web installer's release** (D:\ilomilo\ilomilo-nx-installer, commit 032c89b, local): make_release.py --version
  0.1.0 with Title Update #1 and the 16 records (218 shaders: 83 in default.xex, 135 in the game's files);
  test/full_node.mjs --opus --reference (2 min: 444 variants, 8 banks as .xmop, startup as .opcm, 145 -> 97 MB packed)
  and test/check_zip.py: **OK** (it now checks `.opcm` too: the segments cover the original, every byte outside the
  samples equal); test/check_release.py: git stores the 4 release files the manifest names. Node has no H.265
  encoder, so its zip keeps the movie as it is (ZXC); the page encodes it in the browser.
- **The release NRO in Ryujinx:** emu26 (trial, the media folder) and emu27 (full game, master folder) both drew
  from deko3d_glsl.bin; 60 fps in emu26's 10 s reports (an emulator's figure).
- **Packing** (measured with the installer's own codecs, `out/media/pack_measure.txt`): textures LZ4 55.5 % (ZXC
  no smaller), fonts ZXC 60 %, the PCM bank ZXC 74 % when it is not `.opcm`, the `.par` (deflated), PNGs and the
  executables as they are; the rest LZ4. The XMA banks pack to 98 %: their `.xmop` stays unpacked (the 5 % rule).
- **Totals (PC figures):** audio 80.5 -> about 54.8 MB, the movie 37.0 -> 13.4 MB, textures 95.0 -> 52.7 MB.

## Audio: the stereo check (2026-11-25, blur-nx's port 135)

- `audio1` (`audio_channel_census = true`, the default speaker configuration 0x00010001): per 10 s of gameplay FL and FR
  1,876 frames each, C 106-380, LFE 0, RL 0, RR 0: the game fills the front pair and a little centre.
- `audio2` (`audio_speaker_config = 1`, analog stereo): FL / FR the same, **C still 0-283**, LFE / rears 0. ilomilo does
  not fully mix stereo itself when told (XACT still sends some sounds to the centre), so the setting saves nothing as it
  stands; a per-game patch (blur-nx's tools/stereo_mix.py) is worth it only if audio is near the top of a console
  profile. The base's default stays. `audio_switch_pump_pairs` (+5.3 ms of latency for CPU) is the user's choice: off.

## Shaders (2026-11-24)

- `tools/renut_shader_dump.py` on the image: 83 containers (69 vertex, 14 pixel): Direct3D's, XUI's and the video
  codec's.
- The game's own: ilomilo's `.par` archives are ZIP files (deflate). `tools/ilomilo_shader_files.py` decompresses every
  entry and scans it: **135 unique containers (71 vertex, 64 pixel), all in `startup.par`'s `shaders/xbox/*.fxo`**
  (compiled effects); none in arch0-3.par (arch3's `cache/*.XSCH` hold none), none in the DLC's `dlc1.par`, none in
  the loose files. None of them is in the image's 83.
