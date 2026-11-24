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

## The base's game layer taken out (2026-11-24)

- Katamari's hot lists (`app/src/cpu/hot/localized.txt`, `localized_bulk.txt`, `hand.txt`) emptied; its stage
  diagnostic (`katamari_stage_diag.cpp`) and movie hook (`katamari_wmv_ffmpeg.cpp`, Katamari's addresses) not built;
  the build stamp's game name and the Switch's fallback NRO path are ilomilo-nx's.
- `tools/ilomilo_hook_collisions.py` (new): every hook in `app/src` that names a guest function by address, against
  this game's function table. Of 468, two are at a function start of ilomilo, both N&B's widescreen hook in Renut's
  tree (`renut_engine/gpu/guest/widescreen.cpp`, `sub_821D55E8`); the rest name no ilomilo function (the link
  catches those that are built).
