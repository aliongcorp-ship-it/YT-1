# START HERE — INKWITNESS launch pack

Everything for the channel and the first episode. Two links, then a checklist.

| Deliverable | Where |
|---|---|
| **Finished video (5:43, 1080p)** | Google Drive → `INKWITNESS / EP01 - Pisces III (1973) / EP01-inkwitness-1575-ft-1080p-FINAL.mp4` |
| **All channel + video files** | Google Drive folder → `INKWITNESS` |
| Source of truth (code, script, prompts) | this repo, PR #1 |

---

## What was built, in the order you asked for

### 1. Channel identity — **INKWITNESS**
- Handle to claim: **`@inkwitness`**
- Tagline: *True stories that almost disappeared.*
- Full channel description, keywords, content pillars and a growth plan: `brand/channel-identity.md`
- The name was chosen against the actual 2026 market: the stickman-explainer lane is crowded and audiences are now openly rejecting its "ancient humans / every X explained" output as slop. "Ink" promises drawing, "Witness" promises evidence, and it gives the character a job.

### 2. Channel art
- Avatar: `brand/logo/profile-1024.png` (built for the circle crop)
- Banner: `brand/logo/banner-2560.png` (art sits inside the 1546×423 TV-safe area)
- Palette, type, art direction, voice rules: `brand/brand-kit.md`

### 3. The main character — **Wick**
- Model sheet: `brand/character/wick-character-sheet.png`
- Bible: `brand/character/wick-bible.md`
- Rule: he is 6–10% of frame height, he carries the only light, he never speaks, he never touches the story. He is the witness, not the hero.

### 4. Episode 01 — *1,575 Feet Down. 12 Minutes of Air Left.*
The rescue of Roger Mallinson and Roger Chapman from the submersible **Pisces III**, 29 August – 1 September 1973. The deepest successful submersible rescue ever completed. Two men, 480 m down, 76 hours, 12 minutes of oxygen left when the hatch opened.

- Script **with a fact-verification table**: `episodes/ep01-pisces-iii/script/script.md`
- 10 hand-inked plates + the exact prompts: `episodes/ep01-pisces-iii/images/`
- Narration (6 scenes, no music, per your direction): `episodes/ep01-pisces-iii/audio/`
- Subtitles: `episodes/ep01-pisces-iii/subtitles/en.srt` (105 cues, two lines max)

### 5. Packaging — researched, not guessed
`episodes/ep01-pisces-iii/seo/UPLOAD-COPY-PASTE.md` has title, description, tags, hashtags, settings and the pinned comment, ready to paste. The reasoning behind each choice, with sources, is in `seo/README.md`.

**Title:** `1,575 Feet Down. 12 Minutes of Air Left.`
**Hashtags:** `#documentary #truestory #deepsea`

---

## Upload checklist

1. Create the channel, claim `@inkwitness`, paste the description from `UPLOAD-COPY-PASTE.md`, upload avatar + banner.
2. Upload `EP01-inkwitness-1575-ft-1080p-FINAL.mp4`.
3. Paste title, description, tags, hashtags.
4. Upload `EP01-en.srt` as English subtitles (not auto-generated).
5. Set: Not made for kids · Education · **Altered content: yes** (synthetic narration).
6. Upload `EP01-thumbnail-1280x720.png`, then pin the prepared comment.
7. Do not touch the title for 7 days.

---

## Rebuilding anything

```bash
pip install --break-system-packages pillow numpy imageio-ffmpeg fonttools brotli
python3 tools/build.py ep01-pisces-iii      # graphics -> film -> srt -> chapters
```

The renderer needs no system ffmpeg (it ships its own static binary), the fonts are bundled and OFL-licensed, and every word on screen is typeset in code rather than generated — which is the structural reason this does not look like the slop it is competing with.
