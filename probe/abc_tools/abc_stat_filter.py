"""Pre-filter ABC stat chunk -> candidate model IDs. ABC stat yml keys are quoted: '#verts', '#parts'.
Filter: mesh verts in [30k,40k] AND single part (#parts==1, avoids multi-component). Vertex count is
approximate (mesh check in Step 5 is authoritative). Usage: python abc_stat_filter.py <stats_dir>"""
import os, re, sys, glob
STAT_DIR = sys.argv[1] if len(sys.argv) > 1 else "abc_stats"
ymls = glob.glob(os.path.join(STAT_DIR, "**", "*stat*.yml"), recursive=True)
print(f"found {len(ymls)} yml files")
def geti(txt, key):
    m = re.search(r"'?#?" + key + r"'?\s*:\s*(\d+)", txt)
    return int(m.group(1)) if m else None
ids, hist, kept_detail = [], {}, []
for y in ymls:
    txt = open(y, errors="ignore").read()
    v = geti(txt, "verts"); parts = geti(txt, "parts")
    if v is None: continue
    hist[v // 10000] = hist.get(v // 10000, 0) + 1
    if 30000 <= v <= 40000 and (parts == 1 or parts is None):
        mid = re.search(r"(\d{8})", os.path.basename(y))
        if mid:
            ids.append(mid.group(1))
            sharp = geti(txt, "sharp") or 0
            kept_detail.append((mid.group(1), v, sharp))
ids = sorted(set(ids))
open("cand_ids.txt", "w", newline="\n").write("\n".join(ids) + ("\n" if ids else ""))
print(f"vertex histogram (x10k): {dict(sorted(hist.items())[:12])} ...")
print(f"{len(ids)} candidates: #verts in [30k,40k] AND #parts==1 -> cand_ids.txt")
kept_detail.sort(key=lambda r: -r[2])   # most sharp edges first = most mechanical detail
print("top-8 by #sharp (mechanical detail):")
for mid, v, sh in kept_detail[:8]: print(f"  {mid}  verts={v}  sharp={sh}")
