# INKWITNESS — repo

Production repo for the INKWITNESS YouTube channel: brand kit, character bible, per-episode scripts, plates, subtitles, SEO and the render pipeline that turns the plates into a finished 1080p video.

## What's in here

```
brand/
  channel-identity.md     name, handle, channel description, pillars, growth plan
  brand-kit.md           palette, type, art direction, voice, audio spec
  character/             Wick model sheet + character bible
  logo/                  avatar + channel banner (+ raw art)
  fonts/                 Fraunces + Inter Tight (SIL OFL, commercial-safe)
episodes/
  ep01-pisces-iii/
    script/narration.json    single source of truth: scene text, plate mapping, weights
    script/script.md         shooting script (VO + shot description)
    images/                 10 ink plates + PROMPTS.md (style + per-plate prompts)
    subtitles/en.srt        generated
    seo/                    title, description, tags, hashtags, thumbnail copy, A/B plan
    video/                  render output (git-ignored, delivered via Google Drive)
tools/
  make_graphics.py        avatar, banner, title card, end card, thumbnail (typeset in code)
  render.py               Ken Burns + xfade + grain/grade + narration mix + SRT
  build.py                one-command build: graphics → video → srt → metadata with real timestamps
assets/textures/          paper grain overlay
```

## Requirements

Everything runs with no system packages:

```
pip install --break-system-packages pillow numpy imageio-ffmpeg fonttools brotli
```

`imageio-ffmpeg` ships a static ffmpeg 7 binary, so there is no `apt install` step.

## Build an episode

```
python3 tools/build.py ep01-pisces-iii
```

Outputs:
- `episodes/<slug>/video/<slug>-1080p.mp4`
- `episodes/<slug>/subtitles/en.srt`
- `episodes/<slug>/seo/description-final.txt` (chapters with real timestamps)
- `episodes/<slug>/video/timeline.json`

## Rendering rules (the short version)

- 1920×1080, 30 fps, H.264 CRF 18, `+faststart`.
- Each plate gets a slow Ken Burns move (8–12%) whose direction alternates; 0.9 s ink dissolve between plates.
- Grade + grain + vignette are applied **once** over the whole film, after the dissolves, so the paper feels continuous.
- Narration is generated per scene, then placed on the timeline at the exact start of that scene's first plate. Nothing is stretched to fit.
- Text never comes from an image model. Titles, cards and thumbnails are typeset with Pillow in the brand fonts.

## Fact policy

Every number in an episode must appear in a source listed at the bottom of `script.md`. If a source conflicts with another (e.g. 12 vs 20 minutes of remaining oxygen), the script uses the figure from the primary record and the description credits it. This is the difference between a documentary and slop.
