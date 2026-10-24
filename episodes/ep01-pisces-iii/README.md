# EP01 — *Pisces III*, 1973

**Packaged title:** `1,575 Feet Down. 12 Minutes of Air Left.`
**Runtime:** 5:43 · 10 hand-inked plates · narration only (no music bed)

| What | Where |
|---|---|
| Shooting script + fact table | `script/script.md` |
| Machine-readable manifest (scene text, plate mapping, motions) | `script/narration.json` |
| Plates (10) and prompt log | `images/`, `images/PROMPTS.md` |
| Narration audio, one file per scene | `audio/s1…s6.mp3` |
| Subtitles | `subtitles/en.srt` |
| Packaging research, title, tags, description | `seo/README.md`, `seo/description-final.txt` |
| Thumbnail 1280×720 | `seo/thumbnail-1280.png` |
| Finished film | `video/inkwitness-ep01-1080p.mp4` (git-ignored, delivered via Drive) |

## Rebuild

```bash
python3 tools/render.py ep01-pisces-iii --out inkwitness-ep01-1080p.mp4   # film + srt + timeline
python3 tools/make_graphics.py thumb ep01-pisces-iii                     # thumbnail only
python3 tools/build.py ep01-pisces-iii                                   # everything incl. chapters
```

## The two production rules that make this not slop

1. **Every plate obeys one medium** (ink, charcoal, cold-press paper, one amber light, one rust accent). No style drift between shots, because the base prompt block is copied verbatim.
2. **No generated text, ever.** Cards, thumbnails, captions and chapters are typeset in the brand fonts by `tools/make_graphics.py` and `tools/build.py`. Mangled letterforms are the loudest signal of machine-made video, and we remove them structurally rather than hoping the model behaves.

## Next episode (already teased on the end card)

**EP02 — The Byford Dolphin.** 1 November 1985, North Sea. Four divers in a pressurised chamber, one technician at the door, one bad seal. Same clock-driven structure, same ink, colder story.
