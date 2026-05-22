#!/usr/bin/env python3
"""
Add model titles to a side-by-side feedforward comparison video, prepend the
last frame for a seamless loop start, and export a high-quality MP4.

Usage:
    python label_feedforward_comparison.py feedforward_comparison.mov
    python label_feedforward_comparison.py feedforward_comparison.mov -o output.mp4
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    fps: float
    frame_count: int
    has_audio: bool


def _default_font() -> str | None:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if Path(path).is_file():
            return path
    return None


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _probe_video(path: Path) -> VideoInfo:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-count_packets",
        "-show_entries",
        "stream=codec_type,width,height,r_frame_rate,nb_read_packets",
        "-of",
        "json",
        str(path),
    ]
    payload = json.loads(subprocess.check_output(cmd, text=True))
    streams = payload["streams"]
    video = next(stream for stream in streams if stream.get("codec_type") == "video")
    has_audio = any(stream.get("codec_type") == "audio" for stream in streams)

    num, den = video["r_frame_rate"].split("/")
    fps = float(num) / float(den)

    return VideoInfo(
        width=int(video["width"]),
        height=int(video["height"]),
        fps=fps,
        frame_count=int(video["nb_read_packets"]),
        has_audio=has_audio,
    )


def _escape_drawtext(text: str) -> str:
    return text.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")


def build_drawtext_filter(
    left_title: str,
    right_title: str,
    *,
    bottom_title: str,
    fontfile: str | None,
    fontsize: int,
    bottom_fontsize: int,
    y_fraction: float,
    bottom_y_fraction: float,
) -> str:
    font_arg = f"fontfile={fontfile}:" if fontfile else ""
    y_expr = f"h*{y_fraction:.4f}"
    bottom_y_expr = f"h*{bottom_y_fraction:.4f}-text_h"

    def drawtext(title: str, x_expr: str, *, size: int, y: str) -> str:
        escaped = _escape_drawtext(title)
        return (
            f"drawtext={font_arg}text='{escaped}':"
            f"fontsize={size}:fontcolor=white:borderw=3:bordercolor=black:"
            f"x={x_expr}:y={y}"
        )

    left = drawtext(left_title, "(w/4-text_w/2)", size=fontsize, y=y_expr)
    right = drawtext(right_title, "(3*w/4-text_w/2)", size=fontsize, y=y_expr)
    bottom = drawtext(
        bottom_title,
        "(w-text_w)/2",
        size=bottom_fontsize,
        y=bottom_y_expr,
    )
    return f"{left},{right},{bottom}"


def _encode_args(*, crf: int, preset: str) -> list[str]:
    return [
        "-c:v",
        "libx264",
        "-crf",
        str(crf),
        "-preset",
        preset,
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
    ]


def label_comparison_video(
    input_path: Path,
    output_path: Path,
    *,
    left_title: str = "vggt_omega",
    right_title: str = "lingbot_map",
    bottom_title: str = "https://github.com/mimiaigen/vibephysics",
    fontsize: int = 64,
    bottom_fontsize: int = 40,
    y_fraction: float = 0.03,
    bottom_y_fraction: float = 0.96,
    fontfile: str | None = None,
    crf: int = 16,
    preset: str = "slow",
) -> None:
    fontfile = fontfile or _default_font()
    vf = build_drawtext_filter(
        left_title,
        right_title,
        bottom_title=bottom_title,
        fontfile=fontfile,
        fontsize=fontsize,
        bottom_fontsize=bottom_fontsize,
        y_fraction=y_fraction,
        bottom_y_fraction=bottom_y_fraction,
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        vf,
        *_encode_args(crf=crf, preset=preset),
        "-an",
        str(output_path),
    ]

    print(f"Labeling {input_path} -> {output_path}")
    print(f"  left title:   {left_title!r} (top center of left panel)")
    print(f"  right title:  {right_title!r} (top center of right panel)")
    print(f"  bottom title: {bottom_title!r} (bottom center)")
    _run(cmd)


def prepend_last_frame_and_export_mp4(
    input_path: Path,
    output_path: Path,
    *,
    crf: int = 16,
    preset: str = "slow",
) -> None:
    info = _probe_video(input_path)
    frame_duration = 1.0 / info.fps

    print(f"Prepending last frame and exporting MP4: {input_path} -> {output_path}")
    print(f"  frames: {info.frame_count}, fps: {info.fps:.3f}, crf: {crf}, preset: {preset}")

    with tempfile.TemporaryDirectory(prefix="feedforward_video_") as tmp_dir:
        tmp = Path(tmp_dir)
        last_png = tmp / "last_frame.png"
        last_clip = tmp / "last_frame.mp4"

        _run(
            [
                "ffmpeg",
                "-y",
                "-sseof",
                "-0.2",
                "-i",
                str(input_path),
                "-frames:v",
                "1",
                "-update",
                "1",
                str(last_png),
            ]
        )

        _run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-framerate",
                f"{info.fps:.6f}",
                "-t",
                f"{frame_duration:.6f}",
                "-i",
                str(last_png),
                *_encode_args(crf=crf, preset=preset),
                "-an",
                str(last_clip),
            ]
        )

        filter_parts = [
            "[0:v]setpts=PTS-STARTPTS[v0]",
            "[1:v]select='eq(n\\,0)',setpts=PTS-STARTPTS[v1]",
            "[v1][v0]concat=n=2:v=1:a=0[vout]",
        ]
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-i",
            str(last_clip),
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            "[vout]",
            *_encode_args(crf=crf, preset=preset),
            "-an",
            str(output_path),
        ]
        _run(cmd)


def process_comparison_video(
    input_path: Path,
    output_path: Path,
    *,
    left_title: str = "vggt_omega",
    right_title: str = "lingbot_map",
    bottom_title: str = "https://github.com/mimiaigen/vibephysics",
    fontsize: int = 64,
    bottom_fontsize: int = 40,
    y_fraction: float = 0.03,
    bottom_y_fraction: float = 0.96,
    fontfile: str | None = None,
    crf: int = 16,
    preset: str = "slow",
    skip_labels: bool = False,
) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found. Install ffmpeg to label comparison videos.")

    output_path = output_path.with_suffix(".mp4")

    with tempfile.TemporaryDirectory(prefix="feedforward_video_") as tmp_dir:
        labeled_path = Path(tmp_dir) / "labeled.mp4"
        source = input_path

        if skip_labels:
            labeled_path = input_path
        else:
            label_comparison_video(
                input_path,
                labeled_path,
                left_title=left_title,
                right_title=right_title,
                bottom_title=bottom_title,
                fontsize=fontsize,
                bottom_fontsize=bottom_fontsize,
                y_fraction=y_fraction,
                bottom_y_fraction=bottom_y_fraction,
                fontfile=fontfile,
                crf=crf,
                preset=preset,
            )
            source = labeled_path

        prepend_last_frame_and_export_mp4(
            source,
            output_path,
            crf=crf,
            preset=preset,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Label a side-by-side feedforward comparison video, prepend the last "
            "frame, and export a high-quality MP4."
        )
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="feedforward_comparison.mov",
        help="Input comparison video (default: feedforward_comparison.mov)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output MP4 path (default: <input_stem>_labeled.mp4)",
    )
    parser.add_argument("--left-title", default="vggt_omega")
    parser.add_argument("--right-title", default="lingbot_map")
    parser.add_argument(
        "--bottom-title",
        default="https://github.com/mimiaigen/vibephysics",
        help="Bottom-center caption (default: repo URL)",
    )
    parser.add_argument("--fontsize", type=int, default=64)
    parser.add_argument("--bottom-fontsize", type=int, default=40)
    parser.add_argument(
        "--y-fraction",
        type=float,
        default=0.03,
        help="Vertical title position as a fraction of frame height (default: 0.03)",
    )
    parser.add_argument(
        "--bottom-y-fraction",
        type=float,
        default=0.96,
        help="Bottom caption baseline as a fraction of frame height (default: 0.96)",
    )
    parser.add_argument("--font", default=None, help="Optional path to a .ttf font file")
    parser.add_argument(
        "--crf",
        type=int,
        default=16,
        help="x264 CRF for visually lossless output (lower = higher quality, default: 16)",
    )
    parser.add_argument(
        "--preset",
        default="slow",
        help="x264 preset for better compression at the same quality (default: slow)",
    )
    parser.add_argument(
        "--skip-labels",
        action="store_true",
        help="Only prepend last frame and export MP4 (input already labeled)",
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path = (
        Path(args.output)
        if args.output
        else input_path.with_name(f"{input_path.stem}_labeled.mp4")
    )

    process_comparison_video(
        input_path,
        output_path,
        left_title=args.left_title,
        right_title=args.right_title,
        bottom_title=args.bottom_title,
        fontsize=args.fontsize,
        bottom_fontsize=args.bottom_fontsize,
        y_fraction=args.y_fraction,
        bottom_y_fraction=args.bottom_y_fraction,
        fontfile=args.font,
        crf=args.crf,
        preset=args.preset,
        skip_labels=args.skip_labels,
    )
    print(f"Done: {output_path}")


if __name__ == "__main__":
    main()
