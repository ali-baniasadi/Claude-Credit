# نسخه‌ی العفاسی. زمان‌ها موقتی‌اند و باید با tools/transcribe.sh و تحلیل افت صدا اصلاح شوند.
import os, runpy
_here = os.path.dirname(os.path.abspath(__file__))
_c = runpy.run_path(os.path.join(_here, '_common.py'))
STYLE = 'noore_rezvan'
REF, FULL_AYAH, LABEL = _c['REF'], _c['FULL_AYAH'], _c['LABEL']

AUDIO_SRC = 'library/recitations/alafasy/016_an-nahl_098-100.mp3'  # برش آیات ۹۸ تا ۱۰۰ از 016.mp3
AUDIO_START, AUDIO_END = 0.0, 40.0   # TODO: برش واقعی
END_CARD = (37.0, 40.0)

# TODO: زمان شروع/پایان هر عبارت (ثانیه روی تایم‌لاین ویدیو)
_T = [(0.8, 5.0), (5.0, 12.0), (12.0, 19.0), (19.0, 25.0), (25.0, 31.0), (31.0, 36.5)]
ARABIC = [(a, b, t) for (a, b), t in zip(_T, _c['PHRASES'])]

# تکه‌های ترجمه: هر عبارت (بازه‌ی خودش) بین تکه‌هایش به‌طور مساوی تقسیم می‌شود
CHUNKS = []
_tr = _c['TRANSLATION']
_groups = [_tr[0], _tr[1], _tr[2], _tr[3], _tr[4] + _tr[5], _tr[6]]
for (a, b), chunks in zip(_T, _groups):
    step = (b - a) / len(chunks)
    CHUNKS += [(a + i * step, a + (i + 1) * step, c) for i, c in enumerate(chunks)]

# TODO: فوتیج‌ها از library/footage (فرمت: (شروع, پایان, نام‌فایل‌بدون‌mp4, ثانیه‌ی شروع کلیپ, grade, zoom))
SCENES = [
    # (0.0, 6.0, 'nature/FOOTAGE_NAME', 0, '', (1.0, 1.06)),
]
