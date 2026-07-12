#!/usr/bin/env python3
"""
SHORTS FACTORY - zero-cost vertical video generator (1080x1920)
Renders kinetic-typography Shorts: word-by-word text reveals,
ambient audio bed, progress bar, brand footer. Frames piped to ffmpeg.
"""
import subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BG = (14, 17, 22)
INK = (242, 244, 248)
DIM = (138, 147, 166)
CUBE = [(229,72,77),(247,107,21),(255,197,61),(48,164,108),(62,123,250),(236,237,239)]
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

SCENES = [
    ("Your brain wasn't built for 47 open tabs.", 3.6, 0),
    ("Every unfinished task keeps running in the background.", 4.2, 1),
    ("Psychologists call it the Zeigarnik effect.", 3.6, 4),
    ("The fix isn't discipline. It's a list.", 3.6, 2),
    ("Write every open loop down. Your brain only releases what it trusts is captured.", 5.8, 3),
    ("Then pick one. Just one.", 3.2, 5),
    ("Unscramble your day.", 4.0, 2),
]
BRAND = "UNSCRAMBLE YOUR LIFE"
OUT = sys.argv[1] if len(sys.argv) > 1 else "short.mp4"

if len(sys.argv) > 2:
    import json
    with open(sys.argv[2]) as fh:
        doc = json.load(fh)
    SCENES = [tuple(s) for s in (doc["scenes"] if isinstance(doc, dict) else doc)]
    if isinstance(doc, dict) and doc.get("brand"):
        BRAND = doc["brand"]

def font(sz): return ImageFont.truetype(FONT_PATH, sz)
F_MAIN, F_BRAND, F_TICK = font(86), font(34), font(28)

def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def wrap_words(draw, words, fnt, maxw):
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if draw.textlength(test, font=fnt) <= maxw or not cur:
            cur.append(w)
        else:
            lines.append(cur); cur = [w]
    if cur: lines.append(cur)
    return lines

def render_frame(scene_i, t_in, t_total, global_t, video_len):
    text, dur, ci = SCENES[scene_i]
    accent = CUBE[ci]
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    for k in range(5):
        ph = global_t * 0.12 + k * 1.7
        x = int(W * (0.15 + 0.7 * (0.5 + 0.5 * math.sin(ph))))
        y = int(H * ((0.1 + 0.18 * k + global_t * 0.008) % 1.0))
        s = 46 + k * 10
        c = CUBE[k % 6]
        tile = Image.new("RGB", (s, s), tuple(int(v * 0.22 + BG[j] * 0.78) for j, v in enumerate(c)))
        img.paste(tile, (x, y))

    words = text.split()
    reveal_span = dur * 0.55
    per = reveal_span / max(1, len(words))
    lines = wrap_words(d, words, F_MAIN, W - 200)
    line_h = 112
    block_h = len(lines) * line_h
    y0 = (H - block_h) // 2 - 60

    wi = 0
    for li, line in enumerate(lines):
        total_w = d.textlength(" ".join(line), font=F_MAIN)
        x = (W - total_w) / 2
        for word in line:
            t_word = (t_in - wi * per) / 0.35
            a = ease(t_word)
            if a > 0:
                yoff = int((1 - a) * 40)
                col = tuple(int(INK[j] * a + BG[j] * (1 - a)) for j in range(3))
                if scene_i == len(SCENES) - 1:
                    base = CUBE[wi % 6]
                    col = tuple(int(base[j] * a + BG[j] * (1 - a)) for j in range(3))
                d.text((x, y0 + li * line_h + yoff), word, font=F_MAIN, fill=col)
            x += d.textlength(word + " ", font=F_MAIN)
            wi += 1

    if t_in > reveal_span:
        p = ease((t_in - reveal_span) / 0.5)
        lw = int(220 * p)
        d.rounded_rectangle([(W - lw) // 2, y0 + block_h + 46,
                             (W + lw) // 2, y0 + block_h + 58], 6, fill=accent)

    prog = global_t / video_len
    d.rectangle([0, H - 12, int(W * prog), H], fill=accent)

    bw = d.textlength(BRAND, font=F_BRAND)
    d.text(((W - bw) / 2, H - 110), BRAND, font=F_BRAND, fill=DIM)

    tick = f"{scene_i + 1} / {len(SCENES)}"
    d.text((W - d.textlength(tick, font=F_TICK) - 60, 90), tick, font=F_TICK, fill=DIM)
    return img

def main():
    video_len = sum(s[1] for s in SCENES)
    total_frames = int(video_len * FPS)

    vf = subprocess.Popen([
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i",
        ("aevalsrc=0.05*sin(2*PI*110*t)+0.035*sin(2*PI*164.8*t)"
         "+0.03*sin(2*PI*220*t)*(0.6+0.4*sin(2*PI*0.25*t))"
         f":d={video_len:.2f}"),
        "-af", f"lowpass=f=600,afade=t=in:d=1.5,afade=t=out:st={video_len-2:.2f}:d=2",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-shortest", OUT
    ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    frame_n = 0
    for si, (text, dur, ci) in enumerate(SCENES):
        n = int(dur * FPS)
        for f in range(n):
            t_in = f / FPS
            img = render_frame(si, t_in, dur, frame_n / FPS, video_len)
            if si < len(SCENES) - 1 and t_in > dur - 0.25:
                fade = (t_in - (dur - 0.25)) / 0.25
                img = Image.blend(img, Image.new("RGB", (W, H), BG), fade * 0.85)
            vf.stdin.write(img.tobytes())
            frame_n += 1

    vf.stdin.close()
    vf.wait()
    print(f"Done -> {OUT} ({video_len:.0f}s, {frame_n} frames)")

if __name__ == "__main__":
    main()
