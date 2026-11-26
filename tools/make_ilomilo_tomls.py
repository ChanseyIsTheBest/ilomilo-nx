#!/usr/bin/env python3
"""ilomilo-nx (2026-11-25, from katamari-nx's tools/make_katamari_tomls.py): writes the package's tomls from the base's
shipped renut.toml (tools/base_shipped_renut.toml: dist/switch/katamari-nx/renut.toml at the base's 680dee40, itself banjo-nx's set), with ilomilo's
settings:

  renut.toml       the shipped settings: Renut on deko3d, the picture as the Xbox 360 draws it (720 lines in both modes,
                   no dynamic resolution, post-processing at the game's precision), MSAA at the base's 1 sample (the
                   game's own 4x is a config: the user's decision), every exact enhancement as the base ships it, the
                   items measured SLOWER ON THE CONSOLE off, diagnostics on (logs);
  renut_play.toml  renut.toml with the diagnostics off (no log, no profilers, no stall watchdog, no census);
  renut_ab.toml    renut.toml with an in-run A/B list, 30 s halves, target 1 (a Vulkan-only key: does nothing on the
                   Switch) as the do-nothing control;
  configs/*.toml   the picture-changing options and the test sets, each a few keys away from renut.toml.

The NRO reads one toml: ilomilo.toml next to it (the built-in config's build, the default; renut.toml with
KATAMARI_BUILTIN_CONFIG off). Copy one of these over ilomilo.toml (tools/package_switch.ps1 names the package's copy).

  python tools/make_ilomilo_tomls.py [--base tools/base_shipped_renut.toml] [--out dist/switch/ilomilo-nx]
"""
import argparse
import os
import re

HEADER = """# ilomilo-nx (ilomilo on the Switch, Renut's renderer on deko3d): {what}
# Made by tools/make_ilomilo_tomls.py from the ultimate base's shipped renut.toml. Copy over ilomilo.toml next to the
# NRO, the only toml it reads. Credits: reNut's renderer (masterspike52, reuse permitted), the ultimate base and the ports
# whose fixes it carries, renut-nx, sa2-nx, NetherSX2_nx, battd_nx, bejeweled3-nx and the zuma ports.
"""

# Keys set for ilomilo (the rest as the base ships them).
SHIPPED = {
    'banjo_renderer': '"renut"',
    'renut_gpu_backend': '"deko3d"',
    # The Xbox 360's picture: 720 lines in both modes (the console scales to the TV), no dynamic resolution.
    'banjo_renut_render_height_handheld': '720',
    'banjo_renut_render_height_docked': '1080',  # 2026-11-26: the user's default
    'banjo_renut_display_height_docked': '1080',
    'banjo_renut_dynamic_resolution': 'false',
    # The base's one sample (port 118). ilomilo asks for 4x MSAA (three predicated tiles of 1280x256):
    # configs/renut_msaa4.toml has the game's own count, the user's decision.
    'msaa_level': '1',
    'renut_shadow_resolution': '"1x"',
    'renut_ambient_occlusion': '"Half"',
    'renut_post_process_precision': '"Game"',
    'frame_cap': '"Off"',
    'target_refreshRate': '-1',
    'masseffect_renderer_native': 'false',
    'gpu_plugin': '""',
    # No forwarder for ilomilo yet (three cores); a forwarder the user makes sets its own program id here.
    'banjo_forwarder_program_id': '""',
    'banjo_system_core_uam': 'false',
    'banjo_xma_frame_cache': 'false',
    'banjo_shader_misses': '"sdmc:/switch/ilomilo-nx/shader_misses"',
    # The XBLA licence: the full game (XamContentGetLicenseMask answers "bought"; the SDK's default 0 is the trial).
    'license_mask': '1',
    # SMAA after ilomilo's final composite (the depth-of-field pass, docs/ilomilo-notes.md).
    'banjo_renut_smaa_after_ps': '"0B4973CE2EEC601A"',
    # The four keys decided from this port's log (gameplay windows; docs/ilomilo-notes.md).
    'ultimate_renut_replay_inherit_same': 'false',
    'sasrt_gpu_skip_inert_draws': 'false',
    'banjo_renut_tags_check': '256',
    'banjo_renut_stream_redeem': 'false',
    # The vertex explosions (the menus' and loading cards' backdrop, console and Ryujinx; docs/ilomilo-notes.md): no
    # frame ahead, so the game cannot rewrite vertex data the render thread has yet to read. The user tested it on
    # the console (2026-11-25): "fixes all vertex issues with seemingly little or no cost".
    'rr6_frames_ahead': '0',
}
# Katamari's own keys in the base's file (its hand natives and its DLC switch), not in this port.
DROP = re.compile(r'^\s*(katamari_\w+|banjo_cpu_native_sub_\w+)\s*=.*$\n?', re.M)
PLAY = {'log_level': '"off"', 'log_file_writer': 'false', 'switch_profile_stacks': 'false',
        'banjo_cpu_profiler': 'false', 'banjo_show_profiler': 'false', 'banjo_show_fps': 'false',
        'banjo_stall_watch_seconds': '0', 'renut_gpu_profile': '0.0', 'banjo_renut_diag_resolve_trace': 'false',
        'banjo_renut_diag_gpu_shaders': 'false', 'banjo_renut_diag_terrain': 'false', 'switch_perf_count_calls': 'false'}
# The targets that can act on ilomilo's draws (direct calls, no command-buffer recordings: the census of
# docs/ilomilo-notes.md): the fast draw (25), pipelines by content (28), whole-buffer copies (22), the setters' touch
# compare (26), merged draws (33), mesh objects (42); 1 (a Vulkan-only key) is the do-nothing control on the Switch.
AB = {'banjo_renut_ab_targets': '"25,28,22,26,33,42,1"', 'banjo_renut_ab_s': '30',
      'banjo_renut_dynamic_resolution': 'false'}
VERIFY = {k: 'true' for k in (
    'banjo_renut_fast_draw_verify', 'banjo_renut_resource_objects_verify', 'banjo_renut_fetch_cache_verify',
    'banjo_renut_whole_buffers_verify', 'banjo_renut_persistent_shared_verify', 'banjo_renut_chain_reuse_verify',
    'banjo_renut_snapshot_deltas_verify', 'banjo_renut_store_cards_verify', 'banjo_renut_record_extents_verify')}
VERIFY.update({'banjo_hot_guard_calls': '4000', 'banjo_hot_guard_period': '64', 'banjo_stall_watch_seconds': '0'})
PGO = {'log_level': '"off"', 'switch_profile_stacks': 'false', 'banjo_cpu_profiler': 'false',
       'banjo_show_profiler': 'false', 'banjo_show_fps': 'false', 'banjo_stall_watch_seconds': '0',
       'renut_gpu_profile': '0.0', 'banjo_renut_diag_resolve_trace': 'false', 'banjo_renut_diag_gpu_shaders': 'false',
       'banjo_renut_diag_terrain': 'false', 'banjo_hot_guard_calls': '0', 'banjo_hot_guard_period': '0'}
# A console CPU profile (docs/optimising-functions.md, "Getting a console profile"): the sampler on, its 10 s reports
# per thread and per function (rex_profile.log), with the ELF of the same build to name the samples.
PROFILE = {'banjo_cpu_profiler': 'true', 'switch_profile_stacks': 'true', 'banjo_stall_watch_seconds': '0'}
CONFIGS = {
    'renut_verify.toml': (VERIFY, 'every Renut verify mode on and the machine copies\' guard (emulator / test runs: '
                                  'slow; the log\'s verify lines must count 0 differences)'),
    'renut_pgo.toml': (PGO, 'the shipped settings with only the crash logs (a PGO build\'s toml)'),
    'renut_profile.toml': (PROFILE, 'the shipped settings with the CPU sampler on (a console profile: '
                                    'logs/rex/rex_profile.log, and the ELF of this build)'),
    'renut_msaa4.toml': ({'msaa_level': '4'}, 'the game\'s own 4x MSAA (not the base\'s default: more GPU work)'),
    'renut_msaa2.toml': ({'msaa_level': '2'}, '2x MSAA (between the base\'s 1 and the game\'s 4)'),
    'renut_1080_docked.toml': ({'banjo_renut_render_height_docked': '1080', 'banjo_renut_display_height_docked': '1080'},
                               '1080 lines docked (not pixel-identical: 1.5x the game\'s 720)'),
    'renut_dynamic.toml': ({'banjo_renut_dynamic_resolution': 'true', 'banjo_renut_render_height_docked': '1080',
                            'banjo_renut_display_height_docked': '1080'},
                           'dynamic resolution, 540-720 handheld / 720-1080 docked (not pixel-identical)'),
}


def apply(text, keys):
    """Sets each key: in place where the base has it at the top level, else before the first [section] ([input_p1] /
    [input_p2] stay last: a key after a table header belongs to that table)."""
    first_section = re.search(r'^\[', text, re.M)
    top_end = first_section.start() if first_section else len(text)
    for k, v in keys.items():
        pat = re.compile(r'^(\s*)' + re.escape(k) + r'\s*=.*$', re.M)
        m = pat.search(text, 0, top_end)
        if m:
            text = text[:m.start()] + f'{m.group(1)}{k} = {v}' + text[m.end():]
        else:
            text = text[:top_end].rstrip('\n') + f'\n{k} = {v}\n\n' + text[top_end:]
        first_section = re.search(r'^\[', text, re.M)
        top_end = first_section.start() if first_section else len(text)
    return text


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default=os.path.join(root, 'tools', 'base_shipped_renut.toml'))
    ap.add_argument('--out', default=os.path.join(root, 'dist', 'switch', 'ilomilo-nx'))
    a = ap.parse_args()
    text = open(a.base, encoding='utf-8').read()
    # The base file's own header (the lines before its first key or blank-line block) is replaced by ours.
    text = re.sub(r'\A(#[^\n]*\n)+', '', text)
    text = DROP.sub('', text).replace('sdmc:/switch/katamari-nx/', 'sdmc:/switch/ilomilo-nx/')
    text = text.replace('katamari.toml', 'ilomilo.toml')
    shipped = apply(text, SHIPPED)
    os.makedirs(os.path.join(a.out, 'configs'), exist_ok=True)
    outs = {
        'renut.toml': (shipped, 'the shipped settings with logs, profiler and diagnostics on (720 lines, 1 sample)'),
        'renut_play.toml': (apply(shipped, PLAY), 'renut.toml with the diagnostics off, for playing'),
        'renut_ab.toml': (apply(shipped, AB), 'renut.toml with an in-run A/B list, 30 s halves, target 1 as the '
                                              'do-nothing control (a Vulkan-only key: nothing on the Switch)'),
    }
    for name, (cfg, what) in CONFIGS.items():
        outs[os.path.join('configs', name)] = (apply(shipped, cfg), what)
    for name, (body, what) in outs.items():
        with open(os.path.join(a.out, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(HEADER.format(what=what) + body)
        print(name)


if __name__ == '__main__':
    main()
