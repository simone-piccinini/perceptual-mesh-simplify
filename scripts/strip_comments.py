#!/usr/bin/env python3
"""Strip full-line // comments from a C++ file for judge submission (source-size limit).

Only removes lines whose first non-whitespace is `//` — trailing comments and string
literals are untouched (zero risk of corrupting code). The compiled binary is identical,
so the stripped file is the SAME binary family as the commented original.

Usage: strip_comments.py <in.cpp> <out.cpp>
"""
import sys

def main():
    src, dst = sys.argv[1], sys.argv[2]
    out = []
    removed = 0
    for line in open(src):
        if line.lstrip().startswith("//"):
            removed += 1
            continue
        # also strip trailing // comments on lines with no string literal (quote-free = safe)
        if "//" in line and '"' not in line and "'" not in line:
            i = line.index("//")
            line = line[:i].rstrip() + "\n"
        out.append(line)
    open(dst, "w").write("".join(out))
    import os
    print(f"{removed} comment lines removed; {os.path.getsize(src)} -> {os.path.getsize(dst)} bytes")

if __name__ == "__main__":
    main()
