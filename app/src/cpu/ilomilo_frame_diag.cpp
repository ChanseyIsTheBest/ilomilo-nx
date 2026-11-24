// ilomilo-nx (2026-11-25): a diagnostic of the emulator's frame stall (docs/ilomilo-notes.md, "The first emulator
// runs"). In Ryujinx the game keeps drawing whole frames but its present routine never reaches the Swap after the
// first two frames. ilomilo's frame (sub_82193768, run by the modal loop in sub_821AB3C8) renders through slot 0x44
// of the object at [0x826ACC58] (sub_821F15B8) and presents through slot 0x44 of the presenter at [0x82645070]
// (sub_821F33E8, which ends in D3DDevice_Swap) when that pointer is not null.
//
// With ilomilo_frame_diag = true: the render and present routines are counted, and a host thread logs every 2 s the
// counts and the guest words that decide the present (the presenter, the renderer, the modal loop's frame time, the
// quit flag). Off (the default) the two hooks only call the original: the same code and the same picture.

#include <rex/cvar.h>
#include <rex/hook.h>
#include <rex/logging.h>
#include <rex/ppc.h>
#include <rex/system/kernel_state.h>
#include <rex/system/xmemory.h>
#include <rex/types.h>

#include <atomic>
#include <bit>
#include <chrono>
#include <cstring>
#include <fmt/format.h>
#include <pthread.h>
#include <string>
#include <thread>
#include <unwind.h>

REXCVAR_DEFINE_BOOL(ilomilo_frame_diag, false, "ilomilo/Diagnostics",
                    "Log every 2 s how often ilomilo's render (sub_821F15B8) and present (sub_821F33E8) routines ran "
                    "and the guest words that decide the present (diagnostic of the emulator's frame stall)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

namespace {

std::atomic<uint64_t> g_renders{0};
std::atomic<uint64_t> g_presents{0};
std::atomic<uint32_t> g_last_present_r3{0};

uint32_t GuestWord(uint32_t va) {
  auto* memory = REX_KERNEL_MEMORY();
  if (!memory)
    return 0;
  const auto* p = memory->TranslateVirtual<const uint8_t*>(va);
  if (!p)
    return 0;
  uint32_t v;
  std::memcpy(&v, p, 4);
  return rex::byte_swap(v);
}

void Reporter() {
  uint64_t renders = 0, presents = 0;
  for (;;) {
    std::this_thread::sleep_for(std::chrono::seconds(2));
    const uint64_t r = g_renders.load(std::memory_order_relaxed);
    const uint64_t p = g_presents.load(std::memory_order_relaxed);
    const uint32_t time_bits = GuestWord(0x82645490);  // the modal loop's last frame time (sub_8218FBF0's f1)
    // The scene render's state 0 resumes the device once KeTimeStampBundle.TickCount (the import at 0x820005E4, +16:
    // sub_8218FBE8 -> sub_822748D0) is more than 1000 past the state's stamp ([state+40]).
    const uint32_t bundle = GuestWord(0x820005E4);
    // The scene render's object (sub_821F15B8 calls slot 0x44 of [0x826ACC58]: sub_820F3040 with it as r3): its state
    // (+16 current, +20 next; sub_820F5358 sets them) and state 0's stamp (+40, the TickCount at the state's entry).
    const uint32_t scene = GuestWord(0x826ACC58);
    REXLOG_INFO("[ilomilo_frame_diag] renders {} (+{}), presents {} (+{}); suspended flag [0x826B71FC] = {}; "
                "TickCount [{:08X}+16] = {}; scene object {:08X}: state {} -> {}, stamp {}, frame counter [0x824C7C58] "
                "= {}; frame time [0x82645490] = {:.3f}",
                r, r - renders, p, p - presents, GuestWord(0x826B71FC), bundle, bundle ? GuestWord(bundle + 16) : 0,
                scene, scene ? GuestWord(scene + 16) : 0, scene ? GuestWord(scene + 20) : 0,
                scene ? GuestWord(scene + 40) : 0, GuestWord(0x824C7C58), double(std::bit_cast<float>(time_bits)));
    renders = r;
    presents = p;
  }
}

// A pthread: std::thread throws std::system_error ("Function not implemented") on the Switch's libstdc++ (the first
// run of this diagnostic ended in std::terminate there).
void* ReporterEntry(void*) {
  Reporter();
  return nullptr;
}

void StartReporter() {
  static std::atomic<bool> started{false};
  if (started.exchange(true, std::memory_order_relaxed))
    return;
  pthread_t thread;
  pthread_attr_t attr;
  pthread_attr_init(&attr);
  pthread_attr_setstacksize(&attr, 256 * 1024);
  if (pthread_create(&thread, &attr, ReporterEntry, nullptr) == 0)
    pthread_detach(thread);
  else
    REXLOG_WARN("[ilomilo_frame_diag] the reporter thread could not start");
  pthread_attr_destroy(&attr);
}

}  // namespace

// ---------------------------------------------------------------------------------------------------------------------
// The fix (ilomilo_logo_hold_resume). The scene render's state 0 (the start-up logo; sub_820F3040 at 0x820F31A4) holds
// the logo on screen: on its 2nd frame it presents and suspends the render device (0x820F3300), and each later frame
// of state 0 resumes it once KeTimeStampBundle's TickCount is 1000 past the state's stamp. Only state 0 resumes it. In
// Ryujinx the first frames took about 2 s for four (pipelines compiled on first use): the game's update moved the scene
// to state 5 (then 2) before another state-0 frame ran, and the device stayed suspended for good. The game rendered
// ~500 frames a second from then on and presented none (emu2-emu8, docs/ilomilo-notes.md). The fix ends the hold when
// the scene leaves state 0 with the device still suspended by it: the device's own Resume (slot 0xF8, sub_821F3100),
// called on the render device at the next frame's render (slot 0x44, sub_821F15B8, whose r3 is the device). At normal
// frame rates state 0 resumes it itself first and the fix never acts. Off: the game's own code alone.
REXCVAR_DEFINE_BOOL(ilomilo_logo_hold_resume, true, "ilomilo/Fixes",
                    "End the start-up logo's display hold (the render device suspended by the scene's state 0) when "
                    "the scene leaves state 0 still held: with slow first frames the game's own resume never ran and "
                    "nothing was presented again")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

namespace {
constexpr uint32_t kSceneObject = 0x826ACC58;  // the scene render's object (sub_820F3040's r3); its state at +16
constexpr uint32_t kSuspendedFlag = 0x826B71FC;  // the render device's suspended flag (slot 0xFC, sub_821F3168)
std::atomic<bool> g_logo_hold{false};  // the device is suspended by state 0's hold

uint32_t SceneState() {
  const uint32_t scene = GuestWord(kSceneObject);
  return scene ? GuestWord(scene + 16) : 0xFFFFFFFFu;
}
}  // namespace

REX_EXTERN(__imp__sub_821F3100);

REX_EXTERN(__imp__sub_821F15B8);
REX_HOOK_RAW(sub_821F15B8) {
  if (REXCVAR_GET(ilomilo_frame_diag)) [[unlikely]] {
    StartReporter();
    g_renders.fetch_add(1, std::memory_order_relaxed);
  }
  static const bool fix = REXCVAR_GET(ilomilo_logo_hold_resume);
  if (fix && g_logo_hold.load(std::memory_order_relaxed)) [[unlikely]] {
    const uint32_t state = SceneState();
    if (state != 0 && GuestWord(kSuspendedFlag) != 0) {
      g_logo_hold.store(false, std::memory_order_relaxed);
      REXLOG_INFO("[ilomilo] ilomilo_logo_hold_resume: the scene left the logo's state 0 (now state {}) with the render "
                  "device still suspended by its hold; resumed here (its own resume needs a state-0 frame a second "
                  "after the state began)",
                  state);
      PPCContext saved = ctx;  // r3 is the render device (this call is its slot 0x44): its Resume takes the same r3
      __imp__sub_821F3100(ctx, base);
      ctx = saved;
    }
  }
  __imp__sub_821F15B8(ctx, base);
}

// The scene render ends with "if (!device->slot_0xFC()) device->slot_0x108()" (sub_820F3040 at 0x820F3FEC): slot 0xFC
// (sub_821F3168) returns the render device's suspended flag [0x826B71FC], set by its Suspend (slot 0xF4, sub_821F3098:
// D3D's suspend, sub_8220E458, then the flag 1) and cleared by its Resume (slot 0xF8, sub_821F3100: sub_8220E4F0, then
// 0). In the emulator the flag stays set after the second frame. Each Suspend and Resume is logged with its caller
// (the guest LR) and thread, and sub_82365B50 (the routine that suspends and resumes guest threads and presents
// through D3DDevice_Present itself) at its entry and exit.
namespace {
std::atomic<uint32_t> g_suspend_logs{0};
bool LogMore() {
  return g_suspend_logs.fetch_add(1, std::memory_order_relaxed) < 200;
}

// The guest LR is not kept by this codegen (the diet elides the LR saves), so the caller is named from the host stack:
// the recompiled functions' native return addresses, logged as offsets from this function's own address (the ELF
// gives its address: aarch64-none-elf-nm app/out/switch/renut | grep HostStackAnchor).
struct Frames {
  uintptr_t pc[32];
  int n = 0;
};
_Unwind_Reason_Code Collect(struct _Unwind_Context* context, void* arg) {
  auto* f = static_cast<Frames*>(arg);
  if (f->n >= 32)
    return _URC_END_OF_STACK;
  f->pc[f->n++] = uintptr_t(_Unwind_GetIP(context));
  return _URC_NO_REASON;
}
}  // namespace

extern "C" [[gnu::noinline]] void HostStackAnchor() {
  asm volatile("");
}

namespace {
void LogHostStack(const char* what) {
  Frames f;
  _Unwind_Backtrace(Collect, &f);
  std::string line;
  const uintptr_t anchor = uintptr_t(&HostStackAnchor);
  for (int i = 0; i < f.n; ++i)
    line += fmt::format(" {:+x}", int64_t(f.pc[i]) - int64_t(anchor));
  REXLOG_INFO("[ilomilo_frame_diag] {}: host stack (offsets from HostStackAnchor):{}", what, line);
}
}  // namespace

REX_EXTERN(__imp__sub_821F3098);
REX_HOOK_RAW(sub_821F3098) {
  const bool on = REXCVAR_GET(ilomilo_frame_diag);
  const uint32_t lr = uint32_t(ctx.lr);
  __imp__sub_821F3098(ctx, base);
  // The logo's hold: a Suspend made while the scene is in state 0 (its 2nd frame, 0x820F3300).
  if (SceneState() == 0)
    g_logo_hold.store(true, std::memory_order_relaxed);
  if (on && LogMore()) {
    REXLOG_INFO("[ilomilo_frame_diag] device Suspend (sub_821F3098) from LR {:08X}: flag [0x826B71FC] = {}", lr,
                GuestWord(0x826B71FC));
    LogHostStack("device Suspend");
  }
}

REX_HOOK_RAW(sub_821F3100) {
  const bool on = REXCVAR_GET(ilomilo_frame_diag);
  const uint32_t lr = uint32_t(ctx.lr);
  __imp__sub_821F3100(ctx, base);
  g_logo_hold.store(false, std::memory_order_relaxed);  // resumed (by the game, or by the fix)
  if (on && LogMore()) {
    REXLOG_INFO("[ilomilo_frame_diag] device Resume (sub_821F3100) from LR {:08X}: flag [0x826B71FC] = {}", lr,
                GuestWord(0x826B71FC));
    LogHostStack("device Resume");
  }
}

REX_EXTERN(__imp__sub_82365B50);
REX_HOOK_RAW(sub_82365B50) {
  const bool on = REXCVAR_GET(ilomilo_frame_diag);
  const uint32_t lr = uint32_t(ctx.lr), r3 = ctx.r3.u32, r4 = ctx.r4.u32;
  if (on && LogMore())
    REXLOG_INFO("[ilomilo_frame_diag] sub_82365B50 enters (LR {:08X}, r3 {:08X}, r4 {:08X})", lr, r3, r4);
  __imp__sub_82365B50(ctx, base);
  if (on && LogMore())
    REXLOG_INFO("[ilomilo_frame_diag] sub_82365B50 returns {:08X} (entered with r3 {:08X})", ctx.r3.u32, r3);
}

REX_EXTERN(__imp__sub_821F33E8);
REX_HOOK_RAW(sub_821F33E8) {
  if (REXCVAR_GET(ilomilo_frame_diag)) [[unlikely]] {
    StartReporter();
    g_presents.fetch_add(1, std::memory_order_relaxed);
    g_last_present_r3.store(ctx.r3.u32, std::memory_order_relaxed);
  }
  __imp__sub_821F33E8(ctx, base);
}
