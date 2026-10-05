# Quranic Videos — notes for Claude

Instagram reels (1080x1920, 30fps) of Quran verses for the page **@noore_rezvan**: real footage, recitation audio, and the Persian translation shown in short chunks synced to the recited phrases. Reply to the user in Persian. Folder layout and commands are in `README.md`.

## Workflow for a new video
1. Make `videos/<SSS>_<surah-name>_<AAA>-<AAA>/` (e.g. `065_at-talaq_002-003`). Copy `_common.py` and a version file from `videos/065_at-talaq_002-003/` as the template.
2. **Text:** the user gives the Arabic and Persian translation (usually Elahi Ghomshei). Split the translation into 2–5 word on-screen chunks, and the Arabic into recited phrases.
3. **Audio:**
   - Alafasy: `https://download.quranicaudio.com/qdc/mishari_al_afasy/murattal/<SSS>.mp3`. Word timings come from `https://api.qurancdn.com/api/qdc/audio/reciters/7/audio_files?chapter=<n>&segments=true`. They can be ~1s early, so refine them with loudness dips.
   - Shakernejad tarteel by juz: `https://dl.emadionline.com/Shakernejad/Juz/Shakernejad-Quran-Juz-<NN>.mp3` (32 kbps; the juz 28 file is truncated after 65:4).
   - Find exact phrase boundaries with `tools/transcribe.sh` (whisper) plus RMS-dip analysis. Verify the cut by transcribing it again.
   - Save audio in `library/recitations/<reciter>/` and log it in `library/AUDIO_SOURCES.md`.
4. **Footage:**
   - Reuse `library/footage/` first; check the tags in `INDEX.csv`.
   - For new clips, search Pexels in the browser pane with `/search/videos/<q>/?orientation=portrait`. Read `__NEXT_DATA__` via fetch to get thumbnails and the 1080x1920 file link, then download with curl.
   - Store clips as `library/footage/<theme>/<desc>_<pexelsId>.mp4` and add a row to `INDEX.csv`.
   - Pick moody, documentary-style shots. Avoid music instruments, churches, and other content that is off-tone for Quran.
5. **Timeline:** use about one scene per 2–4 s, roughly one per Arabic phrase.
6. **Render:**
   - Preview: `DYLD_LIBRARY_PATH=/opt/homebrew/lib python3 tools/render.py videos/<p>/<version>.py --preview`
   - Then a full render without `--preview`.
   - Check a contact sheet (`ffmpeg ... tile`) and loudness (`ebur128`, target −14 LUFS).
   - Delete `build/` afterwards.
7. Update the project `notes.md` and `credits.txt`.

## Brand style (`STYLE = 'noore_rezvan'`, default in `tools/render.py`)
- Translation: YekanBakh Bold. Arabic: Azar (`library/fonts/Azar.ttf`, from the user's bought fonts). Reference line: «سوره … _ آیات …».
- No «قرآن کریم» label and no reciter name on screen.
- Bottom row: outline YouTube, Instagram and Telegram icons, then `@noore_rezvan`.
- Anti-copy watermark: `@noore_rezvan` at 8% opacity, widely tracked to 70% of the width, at y=1600.
- Ambient bed: a synthesized calm pad at `level_db=-42`, about 26 dB under the voice. The user wants it very quiet.
- End card: the full Arabic verse plus the reference, about 3 s.
- `STYLE = 'classic'` only reproduces the first delivered versions.

## Boundaries and preferences
- Never clone or imitate a real person's voice. That includes deceased narrators such as Naser Tahmasb. Use genuine recordings only (user-supplied or published).
- The user is on the Pro plan and cares about usage, so reuse library assets, take few screenshots, and use contact sheets instead of many images.
- Name outputs automatically as `output/<project>_<version>.mp4`. Keep earlier versions; make a new version file (e.g. `_v2`) instead of overwriting.
