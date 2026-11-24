ilomilo-nx: ilomilo (Xbox Live Arcade, title 58410A1B, with Title Update #1) on the Nintendo Switch
====================================================================================================

A ReXGlue static recompilation, built from the ultimate base (renut_nx_ultimate_base: katamari-nx with the universal
fixes of the other Renut ports): its SDK fork, its post-codegen CPU passes and reNut's Direct3D-level renderer on
plume's deko3d back end (no NVK, no PM4 ring, no EDRAM model). Your own game files are needed; nothing of the game is in
this package except the recompiled code.

Credits: reNut's renderer by masterspike52 (its author permits its reuse in these ports), the ultimate base and the
ports whose fixes it carries (its README and docs/ultimate-fixes.md name them), renut-nx, sa2-nx (input, CPU items),
NetherSX2_nx by NaGaa95 (the four-core layout, MIT), battd_nx (the GPU arena), bejeweled3-nx and the zuma ports (the
hot-function method). GPL-3.0 where the sources are.

SD card layout
--------------
sdmc:/switch/ilomilo-nx/ilomilo-nx.nro        the program
sdmc:/switch/ilomilo-nx/ilomilo.toml          settings, the only toml the NRO reads (see "The tomls")
sdmc:/switch/ilomilo-nx/game_root/            the game package's files (default.xex, Data/, Media/ ...), extracted
                                              from the LIVE package, PLUS the title update's default.xexp next to
                                              default.xex (the NRO's code is Title Update #1's: without the .xexp
                                              the base image does not match it)
sdmc:/switch/ilomilo-nx/dlc/                  the DLC package ("autumn tale", the LIVE file as it comes, content
                                              type 2), read in place

The tomls
---------
The settings are compiled into the NRO (app/ilomilo_switch_defaults.toml), and it reads one file over them:
ilomilo.toml. A toml under any other name does nothing, so to use one of these, copy it over ilomilo.toml. Delete
ilomilo.toml and the next start writes the player's short default one.

In configs/ (made by tools/make_ilomilo_tomls.py):
renut.toml        the shipped settings with logs, profiler and diagnostics on: Renut on deko3d, the Xbox 360's 720
                  lines in both modes, one sample per pixel (the base's default; the game itself asks for 4x MSAA),
                  every exact enhancement on, the items measured SLOWER ON THE CONSOLE off.
renut_play.toml   the same with the diagnostics off (for playing).
renut_ab.toml     the same with an in-run A/B list, 30 s halves, target 1 as the do-nothing control (a Vulkan-only
                  key). Stay in one place for 10+ minutes; the log's "[renut A/B]" lines give each target.
the others        options that change the picture (renut_msaa4.toml: the game's own 4x MSAA; renut_msaa2.toml;
                  renut_1080_docked.toml; renut_dynamic.toml), and test settings (renut_verify.toml, renut_pgo.toml,
                  renut_profile.toml: the CPU sampler for a console profile).

Cores
-----
The port runs on the three cores a homebrew launch gets (banjo_forwarder_program_id = ""). With a forwarder of your
own, set its id there: the NRO then writes that forwarder's four-core NPDM to
sdmc:/atmosphere/contents/<id>/exefs/main.npdm, and the next launch has CPU 0-3.

Profiling
---------
The ELF (ilomilo-nx.elf) and the source snapshot (source_<commit>.tgz) are the ones this NRO was built from: a console profile
(configs/renut_profile.toml: logs/rex/rex_profile.log) maps to source lines with them.
