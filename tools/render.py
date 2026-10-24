#!/usr/bin/env python3
"""INKWITNESS render pipeline: plates + narration -> 1080p film.

Design decisions that matter:
  * narration is generated per scene and placed at that scene's first frame,
    so nothing is time-stretched to fit a picture;
  * every plate gets its own slow Ken Burns move, alternating direction;
  * grade, paper grain and vignette are applied once over the finished film so
    the whole thing reads as one continuous sheet of paper;
  * all geometry is computed from real measured audio durations.
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
import textwrap

import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = imageio_ffmpeg.get_ffmpeg_exe()

W, H = 1920, 1080
FPS = 30
XFADE = 0.9

MOTIONS = ["in", "pan-left", "out", "pan-right", "in", "pan-up", "out", "pan-down",
           "in", "pan-left", "out", "pan-right"]


def run(args, quiet=True):
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        print("FFMPEG FAILED:\n", " ".join(args[:14]), "...\n", p.stderr[-4000:])
        raise SystemExit(1)
    return p


def probe_duration(path: str) -> float:
    p = subprocess.run([FF, "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not m:
        raise SystemExit(f"could not read duration of {path}\n{p.stderr[-800:]}")
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def ff_escape(path: str) -> str:
    return path.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def build_clip(image: str, duration: float, motion: str, out_path: str, zoom_in: float = 0.12):
    n = max(2, int(round(duration * FPS)))
    src_w, src_h = 2880, 1620  # oversampled so the slow move stays smooth
    cy = "ih/2-(ih/zoom/2)"
    cx = "iw/2-(iw/zoom/2)"

    if motion == "in":
        z = f"1+{zoom_in}*on/{n}"
        x, y = cx, cy
    elif motion == "out":
        z = f"{1 + zoom_in}-{zoom_in}*on/{n}"
        x, y = cx, cy
    elif motion == "pan-left":
        z = f"{1 + zoom_in * 0.8:.3f}"
        x, y = f"(iw-iw/zoom)*on/{n}", cy
    elif motion == "pan-right":
        z = f"{1 + zoom_in * 0.8:.3f}"
        x, y = f"(iw-iw/zoom)*(1-on/{n})", cy
    elif motion == "pan-up":
        z = f"{1 + zoom_in * 0.8:.3f}"
        x, y = cx, f"(ih-ih/zoom)*(1-on/{n})"
    elif motion == "pan-down":
        z = f"{1 + zoom_in * 0.8:.3f}"
        x, y = cx, f"(ih-ih/zoom)*on/{n}"
    else:
        z, x, y = "1", cx, cy

    vf = (
        f"scale={src_w}:{src_h}:force_original_aspect_ratio=increase,"
        f"crop={src_w}:{src_h},"
        f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},"
        f"setsar=1,format=yuv420p"
    )
    run([FF, "-y", "-i", image, "-vf", vf, "-frames:v", str(n), "-r", str(FPS),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-an", out_path])
    return n


def plan(manifest: dict, audio_dir: str, test_mode: bool):
    """Return plates with absolute durations and the timeline."""
    plates = manifest["plates"]
    by_id = {p["id"]: p for p in plates}
    scenes = []
    t = 0.0

    # title card first
    segments = []
    title = manifest.get("title_card")
    if title:
        segments.append({"kind": "card", "image": os.path.join(ROOT, title["image"]),
                         "duration": float(title.get("duration", 3.0)),
                         "motion": "in", "scene": None, "id": "card-title"})

    for idx, sc in enumerate(manifest["scenes"]):
        # plates that have not been generated yet are dropped, weights renormalised
        kept = [(pid, w) for pid, w in zip(sc["plates"], sc.get("weights") or [1] * len(sc["plates"]))
                if os.path.exists(os.path.join(ROOT, by_id[pid]["image"]))]
        if not kept:
            print(f"  [skip] {sc['id']}: no plates on disk yet")
            continue
        if len(kept) != len(sc["plates"]):
            print(f"  [partial] {sc['id']}: {len(kept)}/{len(sc['plates'])} plates present")
        sc["plates"] = [k for k, _ in kept]
        sc["weights"] = [w for _, w in kept]
        audio = os.path.join(audio_dir, f"{sc['id']}.mp3")
        if test_mode or not os.path.exists(audio):
            dur = float(sc.get("test_duration", 30.0))
            has_audio = False
        else:
            dur = probe_duration(audio)
            has_audio = True
        pad = float(sc.get("pad", 0.85))
        scene_span = dur + pad
        ids = sc["plates"]
        weights = sc.get("weights") or [1.0 / len(ids)] * len(ids)
        wsum = sum(weights)
        k = len(ids)
        span_with_overlaps = scene_span + XFADE * (k - 1)
        for j, pid in enumerate(ids):
            d = span_with_overlaps * weights[j] / wsum
            plate = by_id[pid]
            segments.append({
                "kind": "plate", "id": pid, "image": os.path.join(ROOT, plate["image"]),
                "duration": d, "motion": plate.get("motion") or MOTIONS[len(segments) % len(MOTIONS)],
                "scene": sc["id"], "text": sc.get("text", ""), "audio": audio if has_audio else None,
                "audio_dur": dur,
            })
        scenes.append({"id": sc["id"], "audio": audio if has_audio else None,
                       "audio_dur": dur, "title": sc.get("title", sc["id"]),
                       "text": sc.get("text", "")})

    end = manifest.get("end_card")
    if end:
        segments.append({"kind": "card", "image": os.path.join(ROOT, end["image"]),
                         "duration": float(end.get("duration", 6.0)),
                         "motion": "out", "scene": None, "id": "card-end"})

    # absolute start times through the xfade chain
    start = 0.0
    for i, s in enumerate(segments):
        s["start"] = start
        start = start + s["duration"] - (XFADE if i < len(segments) - 1 else 0.0)
    total = start
    return segments, scenes, total


def render(slug: str, test_mode: bool = False, out_name: str | None = None):
    ep_dir = os.path.join(ROOT, "episodes", slug)
    images_dir = os.path.join(ep_dir, "images")
    audio_dir = os.path.join(ep_dir, "audio")
    work = os.path.join(ep_dir, "video", "clips")
    os.makedirs(work, exist_ok=True)
    os.makedirs(os.path.join(ep_dir, "video"), exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)

    with open(os.path.join(ep_dir, "script", "narration.json")) as f:
        manifest = json.load(f)
    for p in manifest["plates"]:
        base = os.path.basename(p["image"])
        if not base.endswith(".png"):
            base += ".png"
        p["image"] = os.path.join("episodes", slug, "images", base)

    segments, scenes, total = plan(manifest, audio_dir, test_mode)
    print(f"[plan] {len(segments)} segments, {total/60:.2f} min")

    # 1. clips
    clips = []
    for i, seg in enumerate(segments):
        out = os.path.join(work, f"clip-{i:02d}.mp4")
        meta = out + ".json"
        key = {"img": seg["image"], "d": round(seg["duration"], 3), "m": seg.get("motion"), "src": os.path.getmtime(seg["image"])}
        cached = os.path.exists(out) and os.path.exists(meta) and json.load(open(meta)) == key
        if not cached:
            build_clip(seg["image"], seg["duration"], seg.get("motion", "in"), out)
            json.dump(key, open(meta, "w"))
        seg["clip"] = out
        clips.append(out)
        print(f"  clip {i:02d} {seg['id']:<22} {seg['duration']:6.2f}s  {seg.get('motion')}")

    # 2. dissolve chain
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    fc = []
    prev = "0:v"
    acc = segments[0]["duration"]
    for i in range(1, len(segments)):
        off = acc - XFADE
        label = f"x{i}"
        fc.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={XFADE}:offset={off:.3f}[{label}]")
        acc = acc + segments[i]["duration"] - XFADE
        prev = label
    chain = os.path.join(work, "chain.mp4")
    run([FF, "-y", *inputs, "-filter_complex", ";".join(fc), "-map", f"[{prev}]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-r", str(FPS),
         "-pix_fmt", "yuv420p", chain])
    print("[dissolve] ok")

    # 3. final: paper grain, grade, vignette, fades + narration mix
    paper = os.path.join(ROOT, "assets/textures/paper-grain.png")
    if not os.path.exists(paper):
        paper = _fallback_paper()

    audio_inputs, afc = [], []
    idx = 2  # 0 = chain, 1 = paper (loop)
    for sc in scenes:
        if not sc["audio"]:
            continue
        seg = next(s for s in segments if s["scene"] == sc["id"])
        ms = int(round(seg["start"] * 1000))
        audio_inputs += ["-i", sc["audio"]]
        afc.append(f"[{idx}:a]adelay={ms}|{ms},aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a{idx}]")
        idx += 1
    n_audio = idx - 2

    if n_audio:
        mix_inputs = "".join(f"[a{i}]" for i in range(2, idx))
        afc.append(f"{mix_inputs}amix=inputs={n_audio}:normalize=0:dropout_transition=0,"
                   f"loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.95,apad[aout]")
        amap = ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    else:
        amap = ["-an"]

    fade_out_st = max(0.0, total - 1.4)
    vfc = (
        f"[0:v]format=rgb24[v0];"
        f"[1:v]scale={W}:{H},format=rgb24[pp];"
        f"[v0][pp]blend=all_mode=softlight:all_opacity=0.11[vb];"
        f"[vb]eq=contrast=1.09:saturation=1.05:gamma=0.97:brightness=-0.006,"
        f"colorbalance=rs=-0.04:bs=0.045:rm=0.015:bm=-0.02:gs=0.01,"
        f"vignette=angle=PI/4.9,"
        f"noise=alls=3:allf=t,"
        f"fade=t=in:st=0:d=0.8,fade=t=out:st={fade_out_st:.2f}:d=1.4,"
        f"format=yuv420p[vout]"
    )
    graph = vfc + (";" + ";".join(afc) if afc else "")

    out_name = out_name or f"{slug}-1080p.mp4"
    out_path = os.path.join(ep_dir, "video", out_name)
    run([FF, "-y", "-i", chain, "-loop", "1", "-i", paper, *audio_inputs,
         "-filter_complex", graph, "-map", "[vout]", *amap,
         "-t", f"{total:.3f}", "-r", str(FPS),
         "-c:v", "libx264", "-preset", "fast", "-crf", "23",
         "-maxrate", "2050k", "-bufsize", "4100k",
         "-x264-params", "aq-mode=3:deblock=-1,-1",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path])
    print("[render]", out_path, f"{os.path.getsize(out_path)/1e6:.1f} MB", f"{total/60:.2f} min")

    timeline = {
        "slug": slug, "total_seconds": round(total, 3), "fps": FPS,
        "segments": [{k: v for k, v in s.items() if k != "clip"} for s in segments],
        "scenes": [{**sc, "start": next(s["start"] for s in segments if s["scene"] == sc["id"])}
                   for sc in scenes if sc["audio"]],
    }
    with open(os.path.join(ep_dir, "video", "timeline.json"), "w") as f:
        json.dump(timeline, f, indent=2)

    write_srt(timeline, os.path.join(ep_dir, "subtitles", "en.srt"))
    shutil.rmtree(work, ignore_errors=True)
    return timeline


def _fallback_paper():
    from PIL import Image
    import numpy as np
    arr = np.random.default_rng(3).normal(128, 22, (H, W, 3)).clip(0, 255).astype("uint8")
    os.makedirs(os.path.join(ROOT, "assets/textures"), exist_ok=True)
    p = os.path.join(ROOT, "assets/textures/paper-grain.png")
    Image.fromarray(arr).save(p)
    return p


# ---------------------------------------------------------------- subtitles

def _fmt(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _sentences(text: str):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def write_srt(timeline: dict, path: str, max_chars: int = 84):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cues = []
    for sc in timeline["scenes"]:
        text = sc.get("text", "")
        sents = _sentences(text)
        if not sents:
            continue
        weights = [max(1, len(s)) for s in sents]
        wsum = sum(weights)
        t = sc["start"]
        dur = sc["audio_dur"]
        for s, w in zip(sents, weights):
            d = dur * w / wsum
            body = textwrap.fill(s, width=52)
            if len(body) > max_chars:
                body = textwrap.fill(s, width=64)
            cues.append((t, t + d, body))
            t += d
    with open(path, "w") as f:
        for i, (a, b, body) in enumerate(cues, 1):
            f.write(f"{i}\n{_fmt(a)} --> {_fmt(b)}\n{body}\n\n")
    print(f"[srt] {len(cues)} cues -> {path}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    slug = args[0] if args else "ep01-pisces-iii"
    test = "--test" in sys.argv
    out = None
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    if test and not out:
        out = "preview-test.mp4"
    render(slug, test_mode=test, out_name=out)
