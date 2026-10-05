# Quran reel renderer (1080x1920, 30fps).
# Usage:
#   DYLD_LIBRARY_PATH=/opt/homebrew/lib python3 tools/render.py videos/<project>/<version>.py [--preview]
# The version file defines the timeline (scenes, text chunks, audio); see videos/*/ for examples.
import os, runpy, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOOTAGE_DIR = os.path.join(ROOT, 'library', 'footage')
W, H, FPS = 1080, 1920, 30
FONTS = os.path.expanduser('~/Library/Fonts/')
if not os.path.isdir(FONTS):
    FONTS = os.path.join(ROOT, 'library', 'fonts') + '/'
XFADE = 0.25         # cross-dissolve between scenes
DEFAULT_AUDIO_FX = 'highpass=f=60'

CFG_PATH = os.path.abspath(sys.argv[1])
PREVIEW = '--preview' in sys.argv  # render a few stills only
globals().update({k: v for k, v in runpy.run_path(CFG_PATH).items() if k.isupper()})
PROJECT_DIR = os.path.dirname(CFG_PATH)
VERSION = os.path.splitext(os.path.basename(CFG_PATH))[0]
BUILD = os.path.join(PROJECT_DIR, 'build', VERSION)
OUT = os.path.join(PROJECT_DIR, 'output', f'{os.path.basename(PROJECT_DIR)}_{VERSION}.mp4')
AUDIO_SRC = os.path.join(ROOT, AUDIO_SRC)
TOTAL = END_CARD[1]
AUDIO_FX = globals().get('AUDIO_FX', DEFAULT_AUDIO_FX)


def font(name, size):
    local = os.path.join(ROOT, 'library', 'fonts', name)
    path = local if os.path.exists(local) else FONTS + name
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


# Visual styles. 'classic' = first versions; 'noore_rezvan' = page branding (handle + social icons)
STYLES = {
    'classic': dict(translation=('Kalameh-Black.ttf', 84), arabic='wm_Naskh Qurani 93 Semi Bold.ttf',
                    arabic_size=(60, 58), label=True, reciter=True, handle=None, y_big=760, y_ref=862),
    'noore_rezvan': dict(translation=('YekanBakh-Bold.ttf', 80), arabic='Azar.ttf',
                         arabic_size=(64, 60), label=False, reciter=False, handle='@noore_rezvan',
                         y_big=790, y_ref=885, watermark=dict(text='@noore_rezvan', y=1600, width=0.70, alpha=0.08),
                         bed=dict(level_db=-42)),
}


def social_icon(kind, s, stroke):
    """Outline icon (white, RGBA) drawn at 4x and downsampled for clean anti-aliasing."""
    k = 4
    S, sw = s * k, max(1, int(round(stroke * k)))
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    white = (255, 255, 255, 255)
    if kind == 'youtube':
        h = S * 0.72
        y0 = (S - h) / 2
        d.rounded_rectangle((sw / 2, y0, S - sw / 2, y0 + h), radius=S * 0.22, outline=white, width=sw)
        cx, cy, r = S * 0.52, S / 2, S * 0.17
        d.polygon([(cx - r * 0.75, cy - r), (cx - r * 0.75, cy + r), (cx + r, cy)], outline=white, width=sw)
    elif kind == 'instagram':
        d.rounded_rectangle((sw / 2, sw / 2, S - sw / 2, S - sw / 2), radius=S * 0.28, outline=white, width=sw)
        r = S * 0.22
        d.ellipse((S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r), outline=white, width=sw)
        r2 = S * 0.05
        d.ellipse((S * 0.75 - r2, S * 0.25 - r2, S * 0.75 + r2, S * 0.25 + r2), fill=white)
    elif kind == 'telegram':
        d.ellipse((sw / 2, sw / 2, S - sw / 2, S - sw / 2), outline=white, width=sw)
        P = lambda x, y: (S * x, S * y)
        d.line([P(0.24, 0.50), P(0.74, 0.30), P(0.65, 0.72), P(0.45, 0.58), P(0.24, 0.50)], fill=white,
               width=sw, joint='curve')
        d.line([P(0.45, 0.58), P(0.74, 0.30)], fill=white, width=sw)
        d.line([P(0.45, 0.58), P(0.46, 0.70), P(0.53, 0.63)], fill=white, width=sw, joint='curve')
    return img.resize((s, s), Image.LANCZOS)


def make_bed(path, dur, level_db, sr=48000, seed=7):
    """Calm ambient pad: slow-breathing Dsus2 drone (detuned sine pairs) + a little filtered 'air'.
    No rhythm or melody, so it sits under recitation. level_db = RMS level in dBFS."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(dur * sr)) / sr
    out = np.zeros((len(t), 2))
    for i, (f, g) in enumerate([(146.83, 1.0), (220.0, 0.8), (293.66, 0.6), (329.63, 0.35), (440.0, 0.25)]):
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * (0.03 + 0.017 * i) * t + rng.uniform(0, 6.28))
        for ch, det in ((0, -0.18), (1, 0.21)):
            ph = rng.uniform(0, 6.28)
            out[:, ch] += g * lfo * (np.sin(2 * np.pi * (f + det) * t + ph) + 0.12 * np.sin(2 * np.pi * 2 * (f + det) * t + ph))
    # air: soft noise (the final low-pass turns it into a gentle hush)
    out += 0.06 * out.std() * rng.standard_normal((len(t), 2))
    out *= np.minimum(1, t / 3.0)[:, None] * np.minimum(1, (dur - t) / 1.5)[:, None]
    rms = np.sqrt(np.mean(out ** 2))
    out *= 10 ** (level_db / 20) / rms
    pcm = (np.clip(out, -1, 1) * 32767).astype('<i2')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', str(sr), '-ac', '2', '-i', '-',
                    '-af', 'lowpass=f=2200,highpass=f=90', path], input=pcm.tobytes(), check=True)


def watermark_layer(text, y, width, alpha):
    """Faint, widely tracked text spanning `width` of the frame (anti-copy watermark)."""
    f = ImageFont.truetype(FONTS + 'Montserrat-SemiBold.ttf', 46)
    target = W * width
    glyphs = sum(f.getlength(c) for c in text)
    track = (target - glyphs) / (len(text) - 1)
    img = Image.new('RGBA', (W, 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = (W - target) / 2
    for c in text:
        d.text((x, 50), c, font=f, fill=(255, 255, 255, int(255 * alpha)), anchor='lm')
        x += f.getlength(c) + track
    a = np.asarray(img, np.float32) / 255
    return a[..., :3] * a[..., 3:4], a[..., 3:4], y - 50


def brand_row(handle, y, icon_size=34, icon_alpha=0.45, text_alpha=0.72):
    """Centered row: [youtube instagram telegram] | @handle  -> blend layer."""
    hf = ImageFont.truetype(FONTS + 'Montserrat-Medium.ttf', 30)
    track = 2
    tw = sum(hf.getlength(c) + track for c in handle) - track
    gap, sep_gap = 16, 22
    icons_w = 3 * icon_size + 2 * gap
    total = icons_w + 2 * sep_gap + 1 + tw
    img = Image.new('RGBA', (W, 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = (W - total) / 2
    for kind in ('youtube', 'instagram', 'telegram'):
        ic = social_icon(kind, icon_size, 2.0)
        a = ic.getchannel('A').point(lambda v: int(v * icon_alpha))
        ic.putalpha(a)
        img.alpha_composite(ic, (int(round(x)), 40 - icon_size // 2))
        x += icon_size + gap
    x += sep_gap - gap
    d.line([(x, 40 - 15), (x, 40 + 15)], fill=(255, 255, 255, int(255 * icon_alpha * 0.8)), width=1)
    x += 1 + sep_gap
    for c in handle:
        d.text((x, 40), c, font=hf, fill=(255, 255, 255, int(255 * text_alpha)), anchor='lm')
        x += hf.getlength(c) + track
    a = np.asarray(img, np.float32) / 255
    al = a[..., 3:4]
    # soft shadow for legibility on bright footage
    sh = np.asarray(img.getchannel('A').filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255 * 0.5
    return a[..., :3] * al, al + sh * (1 - al), y - 40


def text_layer(lines, shadow=True):
    """lines: list of (text, fontobj, y_center, rgba, lang). Returns (premult rgb float, alpha float, y0)."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for txt, f, y, col, lang in lines:
        size = f.size
        # shrink to fit width
        while d.textlength(txt, font=f, direction='rtl', language=lang) > W - 150:
            size -= 2
            f = f.font_variant(size=size)
        d.text((W // 2, y), txt, font=f, fill=col, anchor='mm', direction='rtl', language=lang)
    bbox = img.getbbox()
    if bbox is None:
        return None
    y0 = max(0, bbox[1] - 40)
    y1 = min(H, bbox[3] + 40)
    img = img.crop((0, y0, W, y1))
    a = np.asarray(img, dtype=np.float32) / 255.0
    rgb, al = a[..., :3], a[..., 3:4]
    if shadow:
        sh = img.getchannel('A').filter(ImageFilter.GaussianBlur(12))
        sa = np.asarray(sh, dtype=np.float32)[..., None] / 255.0 * 0.75
        sh2 = img.getchannel('A').filter(ImageFilter.GaussianBlur(3))
        sa2 = np.asarray(sh2, dtype=np.float32)[..., None] / 255.0 * 0.5
        sa = 1 - (1 - sa) * (1 - sa2)
        # composite text over shadow (black)
        out_a = al + sa * (1 - al)
        out_rgb = rgb * al  # shadow is black so contributes 0
        return out_rgb, out_a, y0
    return rgb * al, al, y0


def blend(frame, layer, opacity, dy=0):
    if layer is None or opacity <= 0:
        return
    rgb, al, y0 = layer
    y0 += dy
    h = rgb.shape[0]
    a, b = max(0, y0), min(H, y0 + h)
    if a >= b:
        return
    s = slice(a - y0, b - y0)
    region = frame[a:b]
    region *= (1 - al[s] * opacity)
    region += rgb[s] * opacity


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def chunk_alpha(t, t0, t1, fin=0.28, fout=0.18):
    return smooth((t - t0) / fin) * smooth((t1 - t) / fout)


def open_clip(name, t_in, dur, grade, blur=False):
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
          "eq=contrast=1.06:saturation=0.82,"
          "colorbalance=rs=0.035:gs=0.01:bs=-0.04:rm=0.03:bm=-0.03:rh=0.02:bh=-0.03")
    if grade:
        vf += ',' + grade
    if blur:
        vf += ',gblur=sigma=22'
    vf += ',vignette=angle=PI/4.2'
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{t_in:.3f}', '-i', os.path.join(FOOTAGE_DIR, name + '.mp4'), '-t', f'{dur + 0.5:.3f}',
           '-vf', vf, '-an', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    return subprocess.Popen(cmd, stdout=subprocess.PIPE)


class ClipReader:
    def __init__(self, name, t_in, dur, grade, zoom, blur=False):
        self.p = open_clip(name, t_in, dur, grade, blur)
        self.last = None
        self.n = 0
        self.dur = dur
        self.zoom = zoom

    def frame(self):
        raw = self.p.stdout.read(W * H * 3)
        if len(raw) == W * H * 3:
            self.last = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        f = self.last
        z0, z1 = self.zoom
        z = z0 + (z1 - z0) * min(1.0, self.n / (self.dur * FPS))
        self.n += 1
        if abs(z - 1.0) > 1e-3:
            cw, ch = W / z, H / z
            x0, y0 = (W - cw) / 2, (H - ch) / 2
            f = np.asarray(Image.fromarray(f).resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch)))
        return f.astype(np.float32) / 255.0

    def close(self):
        self.p.stdout.close()
        self.p.kill()


def main():
    st = STYLES[globals().get('STYLE', 'noore_rezvan')]
    big = font(*st['translation'])
    small = font('YekanBakh-Bold.ttf', 34)
    ref_f = font('YekanBakh-Medium.otf', 32) if os.path.exists(FONTS + 'YekanBakh-Medium.otf') else font('YekanBakh-Bold.ttf', 32)
    ar = font(st['arabic'], st['arabic_size'][0])
    ar_end = font(st['arabic'], st['arabic_size'][1])
    cred = font('YekanBakh-Bold.ttf', 26)

    Y_LABEL, Y_BIG, Y_REF, Y_AR, Y_CRED = 668, 760, 862, 1170, 1250
    Y_BIG, Y_REF, Y_BRAND = st['y_big'], st['y_ref'], 1290
    WHITE = (255, 255, 255, 255)
    SOFT = (255, 255, 255, 215)
    GOLD = (236, 214, 170, 255)

    static_lines = [(REF, ref_f, Y_REF, SOFT, 'fa')]
    if st['label']:
        static_lines.insert(0, (LABEL, small, Y_LABEL, SOFT, 'fa'))
    static = text_layer(static_lines)
    cred_l = text_layer([(RECITER, cred, Y_CRED, (255, 255, 255, 150), 'fa')]) if st['reciter'] else None
    brand_l = brand_row(st['handle'], Y_BRAND) if st['handle'] else None
    wm_l = watermark_layer(**st['watermark']) if st.get('watermark') else None
    chunk_l = [(a, b, text_layer([(t, big, Y_BIG, WHITE, 'fa')])) for a, b, t in CHUNKS]
    ar_l = [(a, b, text_layer([(t, ar, Y_AR, GOLD, 'ar')])) for a, b, t in ARABIC]

    # divider line between translation and Arabic
    div = Image.new('RGBA', (W, 6), (0, 0, 0, 0))
    dd = ImageDraw.Draw(div)
    for x in range(W):
        dist = abs(x - W / 2) / 170
        if dist < 1:
            dd.point((x, 3), fill=(236, 214, 170, int(200 * (1 - dist) ** 1.5)))
    da = np.asarray(div, np.float32) / 255
    div_l = (da[..., :3] * da[..., 3:4], da[..., 3:4], 1060)

    # end card
    end_lines = []
    y = 720 if st['label'] else 680
    if st['label']:
        end_lines.append((LABEL, small, 610, SOFT, 'fa'))
    for ln in FULL_AYAH:
        end_lines.append((ln, ar_end, y, GOLD, 'ar'))
        y += 104
    end_lines.append((REF, ref_f, y + 30, SOFT, 'fa'))
    if st['reciter']:
        end_lines.append((RECITER, cred, y + 100, (255, 255, 255, 150), 'fa'))
    end_l = text_layer(end_lines)

    # center readability gradient (soft dark band behind text)
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    band = 1 - 0.38 * np.exp(-((yy - 900) / 380) ** 2)
    top_bot = 1 - 0.25 * (np.clip((260 - yy) / 260, 0, 1) + np.clip((yy - 1600) / 320, 0, 1))
    shade = (band * top_bot).astype(np.float32)

    readers = {}
    times = [i / FPS for i in range(int(TOTAL * FPS))]
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if PREVIEW:
        times = [round((a + b) / 2, 2) for a, b, _ in CHUNKS] + [round(END_CARD[0] + 1.5, 2)]

    enc = None
    if not PREVIEW:
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                                '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-maxrate', '14M', '-bufsize', '28M',
                                '-pix_fmt', 'yuv420p', '-profile:v', 'high', os.path.join(BUILD, 'video_noaudio.mp4')], stdin=subprocess.PIPE)

    rng = np.random.default_rng(1)
    grain = [(rng.standard_normal((H // 2, W // 2, 1)).astype(np.float32) * 0.018) for _ in range(6)]

    for fi, t in enumerate(times):
        frame = None
        for si, (s0, s1, clip, cin, grade, zoom) in enumerate(SCENES):
            if not (s0 - (XFADE if si else 0) <= t < s1 + (0 if si == len(SCENES) - 1 else 0)):
                continue
            if PREVIEW:
                r = ClipReader(clip, cin + t - s0 + (XFADE if si else 0), 0.2, grade, (1, 1))
                f = r.frame(); r.close()
            else:
                if si not in readers:
                    readers[si] = ClipReader(clip, cin, s1 - s0 + XFADE, grade, zoom)
                f = readers[si].frame()
            w = 1.0 if si == 0 else smooth((t - (s0 - XFADE)) / XFADE)
            frame = f.copy() if frame is None else frame * (1 - w) + f * w
        # free finished readers
        for si in list(readers):
            if t >= SCENES[si][1] + 0.05:
                readers[si].close(); del readers[si]

        # end card background: blur + darken crossfade
        e = smooth((t - END_CARD[0]) / 0.6)
        if e > 0:
            small_img = Image.fromarray((frame * 255).astype(np.uint8)).resize((W // 8, H // 8), Image.BILINEAR)
            bl = np.asarray(small_img.filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BICUBIC), np.float32) / 255
            frame = frame * (1 - e) + bl * 0.42 * e

        frame *= shade if e < 1 else 1.0
        g = grain[fi % len(grain)]
        frame += np.repeat(np.repeat(g, 2, 0), 2, 1)

        main_a = (1 - e) * smooth(t / 0.4)
        blend(frame, static, main_a)
        blend(frame, cred_l, main_a * 0.9)
        blend(frame, div_l, main_a)
        blend(frame, brand_l, smooth(t / 0.4))
        blend(frame, wm_l, 1.0)
        for a, b, l in chunk_l:
            if a - 0.01 <= t < b + 0.01:
                al = chunk_alpha(t, a, b, fout=0.18 if b < END_CARD[0] else 0.5)
                dy = int(round(14 * (1 - smooth((t - a) / 0.35))))
                blend(frame, l, al * (1 - e), dy)
        for a, b, l in ar_l:
            if a <= t < b:
                blend(frame, l, chunk_alpha(t, a, b, 0.35, 0.2) * (1 - e))
        if e > 0:
            blend(frame, end_l, smooth((t - END_CARD[0] - 0.3) / 0.8) * smooth((TOTAL - t) / 0.6))
        # global fade in/out
        frame *= smooth(t / 0.3) * smooth((TOTAL - t) / 0.5)

        out = (np.clip(frame, 0, 1) * 255).astype(np.uint8)
        if PREVIEW:
            Image.fromarray(out).save(os.path.join(BUILD, f'preview_{t:05.2f}.jpg'), quality=88)
        else:
            enc.stdin.write(out.tobytes())
            if fi % 60 == 0:
                print(f'{t:.1f}s', flush=True)

    if enc:
        enc.stdin.close(); enc.wait()
        audio = os.path.join(BUILD, 'audio.wav')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(AUDIO_START), '-to', str(AUDIO_END), '-i', AUDIO_SRC,
                        '-af', f'{AUDIO_FX},afade=t=in:d=0.15,afade=t=out:st={AUDIO_END - AUDIO_START - 0.3}:d=0.3,'
                               'apad,loudnorm=I=-14:TP=-1.5:LRA=11',
                        '-t', str(TOTAL), '-ar', '48000', audio], check=True)
        if st.get('bed'):
            bed = os.path.join(BUILD, 'bed.wav')
            make_bed(bed, TOTAL, **st['bed'])
            mixed = os.path.join(BUILD, 'audio_mix.wav')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', audio, '-i', bed, '-filter_complex',
                            '[0][1]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89', '-ar', '48000',
                            mixed], check=True)
            audio = mixed
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(BUILD, 'video_noaudio.mp4'), '-i', audio,
                        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT],
                       check=True)
        print('done', OUT)


if __name__ == '__main__':
    main()
