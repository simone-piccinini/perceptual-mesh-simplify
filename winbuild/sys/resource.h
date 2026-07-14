/* LOCAL-ONLY shim so mein.cpp compiles under MinGW g++ on Windows.
   The submitted file is byte-identical; the judge's Linux gcc resolves the
   real <sys/resource.h>. getrusage() here returns this process's CPU time
   (user+kernel) via GetProcessTimes -> matches what r_elapsed() bills. */
#ifndef _SHIM_SYS_RESOURCE_H
#define _SHIM_SYS_RESOURCE_H
#include <windows.h>

#define RUSAGE_SELF 0

struct rusage {
    struct { long tv_sec; long tv_usec; } ru_utime;
    struct { long tv_sec; long tv_usec; } ru_stime;
};

static inline int getrusage(int who, struct rusage* ru) {
    (void)who;
    FILETIME cr, ex, kt, ut;
    if (!GetProcessTimes(GetCurrentProcess(), &cr, &ex, &kt, &ut)) return -1;
    unsigned long long k = ((unsigned long long)kt.dwHighDateTime << 32) | kt.dwLowDateTime; /* 100ns */
    unsigned long long u = ((unsigned long long)ut.dwHighDateTime << 32) | ut.dwLowDateTime;
    ru->ru_utime.tv_sec  = (long)(u / 10000000ULL);
    ru->ru_utime.tv_usec = (long)((u % 10000000ULL) / 10ULL);
    ru->ru_stime.tv_sec  = (long)(k / 10000000ULL);
    ru->ru_stime.tv_usec = (long)((k % 10000000ULL) / 10ULL);
    return 0;
}
#endif
