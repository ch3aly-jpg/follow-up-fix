import asyncio
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUT_MP4 = ASSETS / "homepage-demo.mp4"
OUT_POSTER = ASSETS / "homepage-demo-poster.png"
OUT_SCRIPT = ASSETS / "homepage-demo-script.txt"

WIDTH = 1280
HEIGHT = 720
FPS = 30

INK = (17, 24, 32)
MUTED = (88, 99, 112)
LINE = (218, 228, 218)
SOFT = (246, 250, 246)
SOFT_GREEN = (238, 248, 238)
GREEN = (7, 139, 54)
GREEN_DARK = (6, 110, 44)
AMBER = (216, 124, 20)
WHITE = (255, 255, 255)

SCRIPT = (
    "Most small trades do not lose jobs because the quote was bad. "
    "They lose them because the follow-up gets buried. "
    "With Follow-Up Fix, you send three to five open quotes in rough notes. "
    "We turn them into one clean chase list: who is due today, who is overdue, "
    "and the exact message to copy. "
    "You send every message yourself from WhatsApp, text, or email. "
    "No CRM to learn, no inbox access, and no card for the trial. "
    "Try it free for seven days. If it helps, keep it for nineteen pounds a month. "
    "If not, no payment needed."
)


def font(size, weight="regular"):
    candidates = {
        "bold": [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ],
        "regular": [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ],
    }[weight]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default(size=size)


FONTS = {
    "brand": font(28, "bold"),
    "h1": font(62, "bold"),
    "h2": font(42, "bold"),
    "h3": font(28, "bold"),
    "body": font(25),
    "body_bold": font(25, "bold"),
    "small": font(18),
    "small_bold": font(18, "bold"),
    "tiny": font(15),
    "tiny_bold": font(15, "bold"),
}


def ease(x):
    x = max(0, min(1, x))
    return 1 - pow(1 - x, 3)


def draw_text(draw, xy, text, fill, font_obj, max_width=None, line_gap=8):
    x, y = xy
    if not max_width:
        draw.text((x, y), text, fill=fill, font=font_obj)
        return y + draw.textbbox((x, y), text, font=font_obj)[3] - y

    words = text.split()
    lines = []
    line = ""
    for word in words:
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=font_obj) <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    for line in lines:
        draw.text((x, y), line, fill=fill, font=font_obj)
        bbox = draw.textbbox((x, y), line, font=font_obj)
        y += bbox[3] - bbox[1] + line_gap
    return y


def round_rect(draw, box, radius=18, fill=WHITE, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def shadow_panel(base, box, radius=20, blur_offset=18):
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    x1, y1, x2, y2 = box
    sdraw.rounded_rectangle(
        (x1 + 8, y1 + blur_offset, x2 + 8, y2 + blur_offset),
        radius=radius,
        fill=(17, 24, 32, 20),
    )
    return Image.alpha_composite(base.convert("RGBA"), shadow).convert("RGB")


def draw_check(draw, x, y, size=16, color=GREEN):
    draw.line((x, y + size * 0.52, x + size * 0.38, y + size, x + size, y), fill=color, width=3)


def draw_brand(draw, x=70, y=52):
    draw.rounded_rectangle((x, y, x + 30, y + 30), radius=4, outline=GREEN, width=3)
    draw_check(draw, x + 7, y + 8, 17, GREEN)
    draw.text((x + 44, y - 2), "Follow-Up Fix", fill=INK, font=FONTS["brand"])


def draw_tracker(draw, x, y, w, h, highlight=0):
    round_rect(draw, (x, y, x + w, y + h), 18, WHITE, LINE, 1)
    draw.rectangle((x, y, x + 100, y + h), fill=(247, 251, 247))
    draw.text((x + 24, y + 24), "Follow-Up Fix", fill=INK, font=FONTS["tiny_bold"])
    menu = ["Today", "Quotes", "Enquiries", "Reviews"]
    for i, item in enumerate(menu):
        yy = y + 66 + i * 42
        fill = SOFT_GREEN if i == 0 else (247, 251, 247)
        round_rect(draw, (x + 18, yy, x + 86, yy + 28), 8, fill, None)
        draw.ellipse((x + 30, yy + 9, x + 40, yy + 19), fill=GREEN if i == 0 else LINE)
        draw.text((x + 48, yy + 5), item, fill=GREEN_DARK if i == 0 else MUTED, font=FONTS["tiny"])

    content_x = x + 125
    draw.text((content_x, y + 24), "This week at a glance", fill=INK, font=FONTS["small_bold"])
    metrics = [("Due today", "6", GREEN), ("Overdue", "4", AMBER), ("Reviews due", "3", GREEN)]
    for i, (label, value, color) in enumerate(metrics):
        mx = content_x + i * ((w - 150) // 3)
        round_rect(draw, (mx, y + 64, mx + 150, y + 130), 10, WHITE, LINE, 1)
        draw.text((mx + 16, y + 78), label, fill=MUTED, font=FONTS["tiny_bold"])
        draw.text((mx + 16, y + 98), value, fill=color, font=FONTS["h3"])

    rows = [
        ("James Walker", "Exterior paint", "Today", "WhatsApp", "Friendly reminder"),
        ("Sarah Taylor", "Kitchen redo", "Today", "SMS", "Ask if they need info"),
        ("Mark Robinson", "Garden tidy", "Overdue", "Email", "Final nudge"),
        ("Emily Green", "End clean", "Tomorrow", "WhatsApp", "Review request"),
    ]
    table_y = y + 156
    draw.rectangle((content_x, table_y, x + w - 24, table_y + 36), fill=SOFT)
    headers = ["Contact", "Job", "Due", "Channel", "Next step"]
    col_x = [content_x + 14, content_x + 190, content_x + 345, content_x + 430, content_x + 540]
    for hx, header in zip(col_x, headers):
        draw.text((hx, table_y + 10), header.upper(), fill=INK, font=FONTS["tiny_bold"])
    for i, row in enumerate(rows):
        yy = table_y + 36 + i * 42
        if i == highlight:
            draw.rectangle((content_x, yy, x + w - 24, yy + 42), fill=(244, 250, 244))
        draw.line((content_x, yy + 42, x + w - 24, yy + 42), fill=LINE, width=1)
        for hx, cell in zip(col_x, row):
            color = AMBER if cell in {"Overdue", "Tomorrow"} else (214, 24, 24) if cell == "Today" else INK
            draw.text((hx, yy + 12), cell, fill=color, font=FONTS["tiny_bold"] if cell in {"Today", "Overdue", "Tomorrow"} else FONTS["tiny"])

    msg_y = y + h - 126
    draw.text((content_x, msg_y), "Message template", fill=INK, font=FONTS["small_bold"])
    round_rect(draw, (content_x, msg_y + 30, x + w - 24, msg_y + 98), 10, WHITE, LINE, 1)
    draw.text(
        (content_x + 16, msg_y + 46),
        "Hi {first_name}, just checking in on the quote I sent over...",
        fill=INK,
        font=FONTS["tiny"],
    )
    round_rect(draw, (x + w - 160, msg_y + 60, x + w - 42, msg_y + 88), 8, GREEN, None)
    draw.text((x + w - 120, msg_y + 66), "Copy", fill=WHITE, font=FONTS["tiny_bold"])


def draw_phone(draw, x, y, w, h):
    round_rect(draw, (x, y, x + w, y + h), 32, (18, 23, 26), None)
    round_rect(draw, (x + 10, y + 14, x + w - 10, y + h - 14), 24, WHITE, None)
    draw.text((x + 28, y + 44), "WhatsApp", fill=GREEN_DARK, font=FONTS["small_bold"])
    messages = [
        ("Quote follow-up", "Hi James, just checking in on the quote..."),
        ("Reply", "Thanks. Can you fit us in next week?"),
    ]
    yy = y + 94
    for i, (label, body) in enumerate(messages):
        fill = SOFT_GREEN if i == 0 else (246, 247, 249)
        round_rect(draw, (x + 26, yy, x + w - 26, yy + 72), 16, fill, None)
        draw.text((x + 42, yy + 14), label, fill=INK, font=FONTS["tiny_bold"])
        draw.text((x + 42, yy + 36), body, fill=MUTED, font=FONTS["tiny"])
        yy += 88
    round_rect(draw, (x + 28, y + h - 76, x + w - 28, y + h - 36), 20, GREEN, None)
    draw.text((x + 90, y + h - 66), "Send", fill=WHITE, font=FONTS["small_bold"])


def base_frame():
    img = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(img)
    draw_brand(draw)
    draw.line((70, 104, WIDTH - 70, 104), fill=LINE, width=1)
    return img, draw


def render_frame(t, duration):
    img, draw = base_frame()
    progress = t / duration

    # Scene timing in seconds.
    scenes = [(0, 6.0), (6.0, 13.2), (13.2, 23.6), (23.6, 32.8), (32.8, duration)]
    scene_idx = next((i for i, (a, b) in enumerate(scenes) if a <= t < b), len(scenes) - 1)
    a, b = scenes[scene_idx]
    local = ease((t - a) / (b - a))

    if scene_idx == 0:
        draw_text(draw, (80, 162), "Stop losing jobs\nafter the quote.", INK, FONTS["h1"], 560, 4)
        draw_text(
            draw,
            (82, 356),
            "Send 3-5 open quotes. We turn them into a private chase list with the exact messages to copy.",
            MUTED,
            FONTS["body"],
            560,
        )
        round_rect(draw, (82, 488, 530, 552), 16, GREEN, None)
        draw.text((128, 506), "Try it free for 7 days", fill=WHITE, font=FONTS["body_bold"])
        mockup = Image.open(ASSETS / "product-mockup.png").convert("RGBA")
        mockup.thumbnail((560, 390))
        img.paste(mockup, (650, 205), mockup)
        draw_text(draw, (730, 590), "No card. No app to learn. No inbox access.", GREEN_DARK, FONTS["small_bold"], 440)

    elif scene_idx == 1:
        draw_text(draw, (82, 150), "Start with messy quote notes.", INK, FONTS["h2"], 560)
        notes = [
            "James / exterior paint / £950 / sent Tue",
            "Sarah / kitchen redo / £1,200 / asked dates",
            "Mark / garden tidy / £280 / no reply",
            "Emily / end clean / review due",
        ]
        for i, note in enumerate(notes):
            y = 250 + i * 76
            round_rect(draw, (86, y, 560, y + 52), 12, SOFT, LINE, 1)
            draw.text((112, y + 15), note, fill=INK, font=FONTS["small"])
        x_offset = int((1 - local) * 90)
        draw_tracker(draw, 660 + x_offset, 142, 520, 456, highlight=2)
        draw.line((610, 370, 642, 370), fill=GREEN, width=4)
        draw.polygon([(642, 370), (626, 358), (626, 382)], fill=GREEN)

    elif scene_idx == 2:
        draw_text(draw, (82, 148), "One calm list tells you what to do today.", INK, FONTS["h2"], 520)
        draw_text(
            draw,
            (84, 272),
            "Who is due. Who is overdue. What message to copy. No CRM migration.",
            MUTED,
            FONTS["body"],
            520,
        )
        draw_tracker(draw, 610, 128, 560, 486, highlight=0 if local < 0.5 else 2)
        pulse = 8 + int(math.sin(t * 6) * 3)
        draw.rounded_rectangle((1010 - pulse, 540 - pulse, 1148 + pulse, 582 + pulse), radius=12, outline=GREEN, width=4)

    elif scene_idx == 3:
        draw_text(draw, (80, 148), "You send the message yourself.", INK, FONTS["h2"], 520)
        draw_text(
            draw,
            (82, 260),
            "We write the nudge. You copy it into WhatsApp, text, or email from your own account.",
            MUTED,
            FONTS["body"],
            520,
        )
        round_rect(draw, (82, 414, 518, 500), 16, SOFT_GREEN, (191, 224, 196), 1)
        draw_check(draw, 112, 446, 18)
        draw.text((150, 438), "No inbox access", fill=GREEN_DARK, font=FONTS["body_bold"])
        draw_phone(draw, 720, 128, 300, 510)
        round_rect(draw, (960, 466, 1148, 522), 18, GREEN, None)
        draw.text((1000, 482), "Reply logged", fill=WHITE, font=FONTS["small_bold"])

    else:
        draw_text(draw, (96, 148), "Proof before payment.", INK, FONTS["h2"], 540)
        draw_text(
            draw,
            (98, 258),
            "Try it free for seven days. If the chase list helps, keep it for £19/month. If not, no payment needed.",
            MUTED,
            FONTS["body"],
            560,
        )
        bullets = ["Weekly chase list", "Copy-ready messages", "Simple Friday prompt", "You stay in control"]
        for i, item in enumerate(bullets):
            y = 400 + i * 46
            draw_check(draw, 104, y + 6, 18)
            draw.text((142, y), item, fill=INK, font=FONTS["body_bold"])
        round_rect(draw, (700, 186, 1130, 536), 26, SOFT_GREEN, (182, 224, 190), 2)
        draw.text((760, 258), "Start instantly", fill=GREEN_DARK, font=FONTS["h2"])
        draw_text(draw, (762, 340), "Send 3-5 rough quotes and get your first chase list.", INK, FONTS["body_bold"], 300)
        round_rect(draw, (762, 456, 1068, 520), 18, GREEN, None)
        draw.text((800, 474), "Try it free for 7 days", fill=WHITE, font=FONTS["body_bold"])

    # Tiny progress rail.
    draw.line((80, HEIGHT - 48, WIDTH - 80, HEIGHT - 48), fill=(230, 236, 230), width=6)
    draw.line((80, HEIGHT - 48, 80 + int((WIDTH - 160) * progress), HEIGHT - 48), fill=GREEN, width=6)
    return img


async def build_voice(path):
    communicate = edge_tts.Communicate(
        SCRIPT,
        voice="en-GB-SoniaNeural",
        rate="-2%",
        pitch="+0Hz",
    )
    await communicate.save(str(path))


def duration_seconds(ffmpeg, media_path):
    proc = subprocess.run(
        [ffmpeg, "-i", str(media_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", proc.stderr)
    if not match:
        raise RuntimeError(f"Could not parse duration for {media_path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def write_video(ffmpeg, video_path, duration):
    frame_count = int(math.ceil(duration * FPS))
    proc = subprocess.Popen(
        [
            ffmpeg,
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{WIDTH}x{HEIGHT}",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            "19",
            str(video_path),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for idx in range(frame_count):
        frame = render_frame(idx / FPS, duration)
        if idx == 0:
            frame.save(OUT_POSTER)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    _, err = proc.communicate()
    if proc.returncode:
        raise RuntimeError(err.decode("utf-8", errors="ignore"))


def mux(ffmpeg, video_path, audio_path, output_path):
    proc = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-shortest",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="ignore"))


def main():
    ASSETS.mkdir(exist_ok=True)
    OUT_SCRIPT.write_text(SCRIPT + "\n", encoding="utf-8")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / "narration.mp3"
        video = Path(tmp) / "silent.mp4"
        asyncio.run(build_voice(audio))
        duration = duration_seconds(ffmpeg, audio) + 0.4
        write_video(ffmpeg, video, duration)
        mux(ffmpeg, video, audio, OUT_MP4)
    print(f"Wrote {OUT_MP4}")
    print(f"Wrote {OUT_POSTER}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(exc, file=sys.stderr)
        raise
