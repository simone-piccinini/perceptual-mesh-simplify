"""Copy solver/main.cpp into .phase0/ and patch the two POSIX-only bits so it compiles
on Windows with `zig c++`. LOCAL DEV ONLY — never submit the patched file; the real
judge (Linux) needs the original getrusage timer.

Patches:
  1. drop `#include <sys/resource.h>`  (not present on the Windows toolchain)
  2. r_elapsed(): getrusage CPU seconds -> std::chrono wall-clock seconds since g_t0
     (locally we only need *a* monotonic clock for the refine time-box)

Run:  py scripts/phase0/patch_solver_win.py
Out:  .phase0/c3_solver.cpp   (then compile it — see RUNBOOK.md)
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORK = REPO / ".phase0"; WORK.mkdir(exist_ok=True)
src = (REPO / "solver" / "main.cpp").read_text(encoding="utf-8")

INC = "#include <sys/resource.h>\n"
OLD = ("    struct rusage ru; getrusage(RUSAGE_SELF, &ru);\n"
       "    return ru.ru_utime.tv_sec + ru.ru_stime.tv_sec + 1e-6*(ru.ru_utime.tv_usec + ru.ru_stime.tv_usec);")
NEW = "    return std::chrono::duration<double>(std::chrono::steady_clock::now() - g_t0).count();"

if INC not in src:
    print("WARN: sys/resource.h include not found — solver may already be patched or changed.")
else:
    src = src.replace(INC, "")
if OLD not in src:
    print("WARN: getrusage r_elapsed body not found — patch the timer by hand (search 'getrusage').")
else:
    src = src.replace(OLD, NEW)

out = WORK / "c3_solver.cpp"
out.write_text(src, encoding="utf-8")
print(f"wrote {out.relative_to(REPO)}  (patched for local Windows build)")
