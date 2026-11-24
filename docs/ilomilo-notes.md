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

## SMAA (2026-11-25)

The final composite: `banjo_renut_diag_draw_log_s = 125` in gameplay (the CG-13 run, two frames of 161 draws): the
scene into the 1280x720 target, a clear, two full-screen rect-list passes into a second target (the depth-of-field
blur: pixel shaders `5D2224AD595D5FCC`, `949ED45F4495B293`), then **`0B4973CE2EEC601A`**, a full-screen pass back into
the main target (the depth-of-field composite), then the HUD (alpha-blended strips and quads). The same in both frames.
`banjo_renut_smaa_after_ps = "0B4973CE2EEC601A"` (built-in settings and the package tomls): the PC's 10 s line then
says "SMAA ... 600 frames" in gameplay. (Menus that draw no depth of field get no SMAA.)

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
