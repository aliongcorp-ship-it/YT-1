#!/usr/bin/env python3
"""One command per episode: graphics -> film -> subtitles -> final metadata.

    python3 tools/build.py ep01-pisces-iii [--skip-render] [--out name.mp4]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))


def fmt(sec: float) -> str:
    sec = int(round(sec))
    h, sec = divmod(sec, 3600)
    m, sec = divmod(sec, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    slug = args[0] if args else "ep01-pisces-iii"
    ep = os.path.join(ROOT, "episodes", slug)
    out_name = None
    if "--out" in sys.argv:
        out_name = sys.argv[sys.argv.index("--out") + 1]

    print(f"=== {slug} ===")
    for job in ("profile", "banner", "paper", "title", "end"):
        subprocess.run([sys.executable, os.path.join(ROOT, "tools/make_graphics.py"), job], check=True)

    import render  # noqa: E402
    timeline = render.render(slug, out_name=out_name)

    subprocess.run([sys.executable, os.path.join(ROOT, "tools/make_graphics.py"), "thumb", slug], check=True)

    # ---- chapters with real timestamps
    chapters_path = os.path.join(ep, "seo", "chapters.json")
    desc_tpl = os.path.join(ep, "seo", "description-template.txt")
    if os.path.exists(chapters_path) and os.path.exists(desc_tpl):
        chapters = json.load(open(chapters_path))
        starts = {sc["id"]: sc["start"] for sc in timeline["scenes"]}
        lines = ["00:00  " + chapters[0]["title"]]
        for ch in chapters[1:]:
            lines.append(f"{fmt(starts[ch['scene']])}  {ch['title']}")
        tpl = open(desc_tpl).read()
        final = tpl.replace("{{CHAPTERS}}", "\n".join(lines))
        final = final.replace("{{RUNTIME}}", fmt(timeline["total_seconds"]))
        out = os.path.join(ep, "seo", "description-final.txt")
        open(out, "w").write(final)
        print(f"[seo] {out}")

    print(f"\ndone · {timeline['total_seconds']/60:.2f} min · {slug}")


if __name__ == "__main__":
    main()
