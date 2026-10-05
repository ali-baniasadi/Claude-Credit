# نسخه‌ی العفاسی. زمان‌ها موقتی‌اند و باید با tools/transcribe.sh و تحلیل افت صدا اصلاح شوند.
import os, runpy
_here = os.path.dirname(os.path.abspath(__file__))
_c = runpy.run_path(os.path.join(_here, '_common.py'))
STYLE = 'noore_rezvan'
REF, FULL_AYAH, LABEL = _c['REF'], _c['FULL_AYAH'], _c['LABEL']

AUDIO_SRC = 'library/recitations/alafasy/016_an-nahl_098-100.mp3'  # برش 16:98..16:100 (از 1959.5s فایل کامل 16.mp3 تا 1994.4s)
AUDIO_START, AUDIO_END = 0.0, 34.9
END_CARD = (35.0, 38.5)

# زمان عبارت‌ها (ثانیه)، از segments معتبر API قرآن‌سی‌دی‌ان (reciter 7) منهای 1959.5؛ مرز آیات با افت صدا تأیید شد
_T = [(0.17, 3.22), (3.22, 10.16), (10.11, 17.28), (17.28, 22.15), (22.13, 28.82), (28.82, 34.90)]
ARABIC = [(a, b, t) for (a, b), t in zip(_T, _c['PHRASES'])]

# تکه‌های ترجمه: بازه‌ی هر عبارت به نسبت طول متن بین تکه‌هایش تقسیم می‌شود
CHUNKS = []
_tr = _c['TRANSLATION']
_groups = [_tr[0], _tr[1], _tr[2], _tr[3], _tr[4] + _tr[5], _tr[6]]
for (a, b), chunks in zip(_T, _groups):
    w = [len(c) + 6 for c in chunks]
    t = a
    for c, wi in zip(chunks, w):
        d = (b - a) * wi / sum(w)
        CHUNKS.append((t, t + d, c))
        t += d

SCENES = [
    (0.0, 3.22, 'nature/mixkit_5039', 4.0, '', (1.0, 1.06)),
    (3.22, 10.11, 'nature/mixkit_22728', 0.0, '', (1.06, 1.0)),
    (10.11, 17.28, 'nature/mixkit_4132', 2.0, '', (1.0, 1.07)),
    (17.28, 22.13, 'nature/mixkit_4998', 3.0, '', (1.07, 1.0)),
    (22.13, 28.82, 'nature/mixkit_3983', 0.0, '', (1.0, 1.05)),
    (28.82, 38.5, 'nature/mixkit_1704', 0.0, '', (1.0, 1.05)),
]
