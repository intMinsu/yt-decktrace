"""Render the README demo card from a locally extracted lecture frame."""

from __future__ import annotations

import argparse
import base64
from pathlib import Path


def render(frame: Path, output: Path) -> None:
    encoded_frame = base64.b64encode(frame.read_bytes()).decode("ascii")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" role="img" aria-labelledby="title description">
  <title id="title">yt-decktrace real-world Whisper demo</title>
  <desc id="description">A changed frame from the 35C3 Introduction to Deep Learning talk beside the extracted frame, transcript, model, and archive statistics.</desc>
  <defs>
    <linearGradient id="background" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0b1220"/>
      <stop offset="1" stop-color="#111827"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#22d3ee"/>
      <stop offset="1" stop-color="#a78bfa"/>
    </linearGradient>
    <clipPath id="frame-clip">
      <rect x="64" y="142" width="1000" height="562.5" rx="22"/>
    </clipPath>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="18" stdDeviation="22" flood-color="#000000" flood-opacity="0.38"/>
    </filter>
  </defs>

  <rect width="1600" height="900" fill="url(#background)"/>
  <circle cx="1510" cy="30" r="280" fill="#7c3aed" opacity="0.13"/>
  <circle cx="90" cy="880" r="260" fill="#0891b2" opacity="0.10"/>

  <text x="64" y="74" fill="#67e8f9" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="23" font-weight="700" letter-spacing="3">REAL-WORLD WHISPER RUN</text>
  <text x="64" y="114" fill="#f8fafc" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="28" font-weight="700">35C3 · Introduction to Deep Learning</text>

  <rect x="64" y="142" width="1000" height="562.5" rx="22" fill="#020617" filter="url(#shadow)"/>
  <image x="64" y="142" width="1000" height="562.5" href="data:image/jpeg;base64,{encoded_frame}" preserveAspectRatio="xMidYMid slice" clip-path="url(#frame-clip)"/>
  <rect x="82" y="658" width="154" height="31" rx="15.5" fill="#020617" opacity="0.88"/>
  <text x="159" y="680" fill="#f8fafc" text-anchor="middle" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">00:08:29</text>

  <rect x="1102" y="142" width="434" height="562.5" rx="22" fill="#172033" stroke="#334155" filter="url(#shadow)"/>
  <text x="1142" y="195" fill="#94a3b8" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="17" font-weight="700" letter-spacing="2">ACTUAL OUTPUT</text>

  <text x="1142" y="259" fill="#f8fafc" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="46" font-weight="800">41:07</text>
  <text x="1142" y="288" fill="#94a3b8" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="18">English lecture</text>
  <line x1="1142" y1="320" x2="1496" y2="320" stroke="#334155"/>

  <text x="1142" y="376" fill="#67e8f9" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="38" font-weight="800">127</text>
  <text x="1242" y="376" fill="#e2e8f0" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="21" font-weight="600">changed frames</text>
  <text x="1142" y="431" fill="#c4b5fd" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="38" font-weight="800">314</text>
  <text x="1242" y="431" fill="#e2e8f0" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="21" font-weight="600">transcript segments</text>
  <line x1="1142" y1="468" x2="1496" y2="468" stroke="#334155"/>

  <text x="1142" y="520" fill="#f8fafc" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="22" font-weight="700">faster-whisper large-v3</text>
  <text x="1142" y="554" fill="#94a3b8" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="18">CUDA · int8_float16</text>

  <rect x="1142" y="591" width="354" height="72" rx="16" fill="#0f172a" stroke="url(#accent)"/>
  <text x="1168" y="621" fill="#94a3b8" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="15" font-weight="700" letter-spacing="1">GPT-READY ARCHIVE</text>
  <text x="1168" y="650" fill="#f8fafc" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="23" font-weight="800">135 files · 6.25 MiB</text>

  <rect x="64" y="755" width="1472" height="2" fill="url(#accent)" opacity="0.85"/>
  <text x="64" y="807" fill="#f8fafc" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="25" font-weight="700">YouTube → changed frames + timestamped transcript → compact LLM context</text>
  <text x="64" y="850" fill="#94a3b8" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="16">Frame: “35C3 – Introduction to Deep Learning,” teubi / media.ccc.de · CC BY 4.0 · extracted and composited by yt-decktrace</text>
</svg>
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frame", type=Path, help="Path to the extracted JPEG frame")
    parser.add_argument("output", type=Path, help="Path to the generated SVG")
    args = parser.parse_args()
    render(args.frame, args.output)


if __name__ == "__main__":
    main()
