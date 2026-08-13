"""Render the three lightweight SVG diagrams used by the README."""

from __future__ import annotations

import argparse
from pathlib import Path

SHARED_DEFS = """
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="9" refY="6" orient="auto">
      <path d="M1 1 L10 6 L1 11 Z" fill="#242424"/>
    </marker>
    <style>
      .title { font: 700 40px 'Arial Rounded MT Bold', 'Trebuchet MS', Arial, sans-serif; fill: #242424; }
      .subtitle { font: 400 20px 'Trebuchet MS', Arial, sans-serif; fill: #5c5c5c; }
      .label { font: 700 23px 'Arial Rounded MT Bold', 'Trebuchet MS', Arial, sans-serif; fill: #242424; }
      .body { font: 400 18px 'Trebuchet MS', Arial, sans-serif; fill: #242424; }
      .small { font: 400 15px 'Trebuchet MS', Arial, sans-serif; fill: #5c5c5c; }
      .caps { font: 700 14px 'Trebuchet MS', Arial, sans-serif; fill: #5c5c5c; letter-spacing: 2px; }
      .mono { font: 400 22px Consolas, 'Courier New', monospace; }
      .light { fill: #ffffff; }
      .dim { fill: #bdbdbd; }
      .flow { fill: none; stroke: #242424; stroke-width: 4; stroke-linecap: round; marker-end: url(#arrow); }
      .thin { fill: none; stroke: #242424; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
    </style>
  </defs>
"""


def document(title: str, description: str, height: int, content: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="{height}" viewBox="0 0 1440 {height}" role="img" aria-labelledby="title description">
  <title id="title">{title}</title>
  <desc id="description">{description}</desc>
{SHARED_DEFS}
  <rect width="1440" height="{height}" fill="#fff9e8"/>
{content}
</svg>
"""


OVERVIEW = """
  <text x="64" y="76" class="title">From lecture video to LLM-ready context</text>
  <text x="64" y="112" class="subtitle">Keep the visual changes and spoken evidence. Leave the repetition behind.</text>

  <!-- Source video -->
  <rect x="64" y="180" width="250" height="310" rx="22" fill="#ffffff" stroke="#242424" stroke-width="3"/>
  <text x="92" y="218" class="caps">YOUTUBE VIDEO</text>
  <rect x="92" y="240" width="194" height="120" rx="12" fill="#242424"/>
  <circle cx="189" cy="300" r="30" fill="#ffd21e"/>
  <path d="M182 284 L182 316 L208 300 Z" fill="#242424"/>
  <line x1="92" y1="391" x2="286" y2="391" stroke="#d9d2c2" stroke-width="8" stroke-linecap="round"/>
  <line x1="92" y1="391" x2="211" y2="391" stroke="#ff8a65" stroke-width="8" stroke-linecap="round"/>
  <circle cx="211" cy="391" r="8" fill="#242424"/>
  <path d="M96 443 L108 432 L120 451 L132 423 L144 454 L156 435 L168 447 L180 427 L192 453 L204 438 L216 448 L228 429 L240 451 L252 436 L282 443" class="thin"/>
  <text x="92" y="472" class="small">slides · screen · speech</text>

  <path d="M332 334 H378" class="flow"/>

  <!-- yt-decktrace engine -->
  <rect x="394" y="210" width="292" height="250" rx="28" fill="#ffd21e" stroke="#242424" stroke-width="4"/>
  <rect x="438" y="255" width="92" height="62" rx="8" fill="#fff9e8" stroke="#242424" stroke-width="3" transform="rotate(-7 484 286)"/>
  <rect x="462" y="260" width="92" height="62" rx="8" fill="#ffffff" stroke="#242424" stroke-width="3"/>
  <path d="M488 277 L488 305 L511 291 Z" fill="#ff8a65" stroke="#242424" stroke-width="2"/>
  <circle cx="577" cy="290" r="8" fill="#242424"/>
  <circle cx="607" cy="290" r="8" fill="#242424"/>
  <circle cx="637" cy="290" r="8" fill="#242424"/>
  <line x1="585" y1="290" x2="599" y2="290" class="thin"/>
  <line x1="615" y1="290" x2="629" y2="290" class="thin"/>
  <text x="540" y="366" text-anchor="middle" class="label">yt-decktrace</text>
  <text x="540" y="401" text-anchor="middle" class="body">extract · transcribe · align</text>

  <path d="M704 334 H750" class="flow"/>

  <!-- Evidence bundle -->
  <rect x="766" y="165" width="346" height="110" rx="18" fill="#bdebea" stroke="#242424" stroke-width="3"/>
  <rect x="795" y="195" width="70" height="48" rx="6" fill="#ffffff" stroke="#242424" stroke-width="3"/>
  <rect x="808" y="184" width="70" height="48" rx="6" fill="#fff9e8" stroke="#242424" stroke-width="3"/>
  <circle cx="832" cy="203" r="8" fill="#ffd21e" stroke="#242424" stroke-width="2"/>
  <path d="M812 227 L832 211 L846 220 L861 204 L875 228" class="thin"/>
  <text x="902" y="211" class="label">Distinct frames</text>
  <text x="902" y="242" class="small">only stable visual changes</text>

  <rect x="766" y="292" width="346" height="110" rx="18" fill="#ffffff" stroke="#242424" stroke-width="3"/>
  <circle cx="834" cy="347" r="30" fill="#ffd21e" stroke="#242424" stroke-width="3"/>
  <path d="M834 328 V347 L848 356" class="thin"/>
  <text x="886" y="339" class="label">[08:29] Dialogue</text>
  <text x="886" y="370" class="small">timestamped speech segments</text>

  <rect x="766" y="419" width="346" height="110" rx="18" fill="#d8c7ff" stroke="#242424" stroke-width="3"/>
  <path d="M805 445 H850 L869 464 V505 H805 Z" fill="#ffffff" stroke="#242424" stroke-width="3"/>
  <path d="M850 445 V464 H869" class="thin"/>
  <text x="895" y="470" class="label">context.md</text>
  <text x="895" y="501" class="small">frames + transcript + links</text>

  <path d="M1130 347 H1176" class="flow"/>

  <!-- LLM target -->
  <rect x="1192" y="230" width="184" height="235" rx="28" fill="#ffb7a7" stroke="#242424" stroke-width="4"/>
  <path d="M1264 277 L1274 300 L1297 310 L1274 320 L1264 343 L1254 320 L1231 310 L1254 300 Z" fill="#ffd21e" stroke="#242424" stroke-width="3"/>
  <path d="M1323 274 L1328 286 L1340 291 L1328 296 L1323 308 L1318 296 L1306 291 L1318 286 Z" fill="#ffffff" stroke="#242424" stroke-width="2"/>
  <text x="1284" y="388" text-anchor="middle" class="label">LLM input</text>
  <text x="1284" y="420" text-anchor="middle" class="small">visual + text</text>
"""


PIPELINE = """
  <defs>
    <marker id="pipeline-arrow" viewBox="0 0 9 9" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M1 1 L8 4.5 L1 8 Z" fill="#242424"/>
    </marker>
    <style>
      .pipeline-flow { fill: none; stroke: #242424; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; marker-end: url(#pipeline-arrow); }
    </style>
  </defs>
  <text x="64" y="76" class="title">Keep changes. Transcribe speech. Align by time.</text>
  <text x="64" y="112" class="subtitle">Two local pipelines turn one video into a shared evidence timeline.</text>

  <!-- Input -->
  <rect x="64" y="275" width="150" height="190" rx="22" fill="#ffffff" stroke="#242424" stroke-width="3"/>
  <rect x="88" y="303" width="102" height="74" rx="10" fill="#242424"/>
  <circle cx="139" cy="340" r="20" fill="#ffd21e"/>
  <path d="M134 329 L134 351 L152 340 Z" fill="#242424"/>
  <text x="139" y="413" text-anchor="middle" class="label">Video</text>
  <text x="139" y="442" text-anchor="middle" class="small">one source</text>

  <!-- Visual lane -->
  <text x="254" y="176" class="caps">VISUAL LANE</text>
  <path d="M214 330 H228 Q238 330 238 320 V238 Q238 228 248 228 H254" class="pipeline-flow"/>
  <rect x="270" y="190" width="166" height="76" rx="16" fill="#bdebea" stroke="#242424" stroke-width="3"/>
  <text x="353" y="223" text-anchor="middle" class="label">FFmpeg</text>
  <text x="353" y="249" text-anchor="middle" class="small">sample at 1 fps</text>
  <path d="M452 228 H488" class="pipeline-flow"/>

  <rect x="504" y="183" width="44" height="78" rx="6" fill="#ebe6dc" stroke="#8d897f" stroke-width="2"/>
  <circle cx="526" cy="209" r="9" fill="#c8c3b8"/>
  <path d="M510 248 L525 228 L537 238 L544 230" stroke="#8d897f" stroke-width="3" fill="none"/>
  <rect x="560" y="183" width="44" height="78" rx="6" fill="#ebe6dc" stroke="#8d897f" stroke-width="2"/>
  <circle cx="582" cy="209" r="9" fill="#c8c3b8"/>
  <path d="M566 248 L581 228 L593 238 L600 230" stroke="#8d897f" stroke-width="3" fill="none"/>
  <rect x="616" y="183" width="44" height="78" rx="6" fill="#fff3ad" stroke="#242424" stroke-width="3"/>
  <circle cx="638" cy="207" r="9" fill="#ff8a65" stroke="#242424" stroke-width="2"/>
  <path d="M622 248 L636 225 L649 239 L656 218" class="thin"/>
  <rect x="672" y="183" width="44" height="78" rx="6" fill="#fff3ad" stroke="#242424" stroke-width="3"/>
  <rect x="681" y="195" width="26" height="17" rx="3" fill="#d8c7ff" stroke="#242424" stroke-width="2"/>
  <path d="M679 248 L693 225 L705 237 L712 221" class="thin"/>

  <path d="M732 228 H768" class="pipeline-flow"/>
  <rect x="784" y="190" width="226" height="76" rx="16" fill="#ffd21e" stroke="#242424" stroke-width="3"/>
  <text x="897" y="223" text-anchor="middle" class="label">Pillow + ImageHash</text>
  <text x="897" y="249" text-anchor="middle" class="small">distance · stability · gap</text>
  <path d="M1026 228 H1062" class="pipeline-flow"/>

  <rect x="1078" y="183" width="58" height="78" rx="7" fill="#fff3ad" stroke="#242424" stroke-width="3"/>
  <circle cx="1107" cy="208" r="10" fill="#ff8a65" stroke="#242424" stroke-width="2"/>
  <path d="M1085 250 L1103 226 L1118 239 L1129 218" class="thin"/>
  <rect x="1148" y="183" width="58" height="78" rx="7" fill="#ffffff" stroke="#242424" stroke-width="3"/>
  <path d="M1156 248 L1171 224 L1183 237 L1198 215" class="thin"/>
  <text x="1078" y="294" class="small">distinct frames</text>

  <!-- Audio lane -->
  <text x="254" y="418" class="caps">SPEECH LANE</text>
  <path d="M214 406 H228 Q238 406 238 416 V472 Q238 482 248 482 H254" class="pipeline-flow"/>
  <rect x="270" y="438" width="246" height="88" rx="16" fill="#ffffff" stroke="#242424" stroke-width="3"/>
  <path d="M294 482 L306 466 L318 499 L330 454 L342 507 L354 470 L366 496 L378 459 L390 501 L402 471 L414 493 L426 463 L438 502 L450 474 L462 493 L492 482" class="thin"/>
  <text x="393" y="555" text-anchor="middle" class="small">audio waveform</text>
  <path d="M532 482 H568" class="pipeline-flow"/>

  <rect x="584" y="438" width="226" height="88" rx="16" fill="#d8c7ff" stroke="#242424" stroke-width="3"/>
  <text x="697" y="477" text-anchor="middle" class="label">faster-whisper</text>
  <text x="697" y="505" text-anchor="middle" class="small">local speech recognition</text>
  <path d="M826 482 H862" class="pipeline-flow"/>

  <rect x="878" y="426" width="284" height="112" rx="16" fill="#ffffff" stroke="#242424" stroke-width="3"/>
  <text x="902" y="460" class="small">[08:29]</text>
  <text x="980" y="460" class="body">A neural network…</text>
  <line x1="902" y1="478" x2="1138" y2="478" stroke="#d9d2c2" stroke-width="2"/>
  <text x="902" y="512" class="small">[08:36]</text>
  <text x="980" y="512" class="body">The output is…</text>

  <!-- Alignment target -->
  <path d="M1218 228 H1228 Q1238 228 1238 238 V368 Q1238 378 1248 378 H1254" class="pipeline-flow"/>
  <path d="M1178 482 H1254" class="pipeline-flow"/>
  <rect x="1266" y="326" width="126" height="190" rx="20" fill="#ffb7a7" stroke="#242424" stroke-width="3"/>
  <text x="1329" y="370" text-anchor="middle" class="caps">ALIGNED</text>
  <line x1="1292" y1="402" x2="1366" y2="402" class="thin"/>
  <circle cx="1311" cy="402" r="8" fill="#ffd21e" stroke="#242424" stroke-width="2"/>
  <circle cx="1347" cy="402" r="8" fill="#bdebea" stroke="#242424" stroke-width="2"/>
  <line x1="1311" y1="402" x2="1311" y2="443" class="thin"/>
  <line x1="1347" y1="402" x2="1347" y2="467" class="thin"/>
  <rect x="1292" y="435" width="38" height="28" rx="4" fill="#fff3ad" stroke="#242424" stroke-width="2"/>
  <rect x="1328" y="459" width="38" height="28" rx="4" fill="#ffffff" stroke="#242424" stroke-width="2"/>
  <text x="1329" y="500" text-anchor="middle" class="small">timeline</text>
"""


USAGE = """
  <text x="64" y="76" class="title">One command builds the evidence bundle</text>
  <text x="64" y="112" class="subtitle">Pixi runs the reproducible environment; yt-decktrace handles the pipeline.</text>

  <!-- Terminal -->
  <rect x="64" y="158" width="1312" height="276" rx="22" fill="#242424" stroke="#242424" stroke-width="3"/>
  <circle cx="98" cy="190" r="8" fill="#ff8a65"/>
  <circle cx="124" cy="190" r="8" fill="#ffd21e"/>
  <circle cx="150" cy="190" r="8" fill="#75d6b2"/>
  <text x="98" y="257" class="mono" fill="#ffd21e">$</text>
  <text x="130" y="257" class="mono" fill="#ffffff">pixi run analyze "YOUTUBE_URL" --asr whisper --language en</text>
  <line x1="98" y1="292" x2="1342" y2="292" stroke="#555555" stroke-width="2"/>

  <circle cx="118" cy="344" r="13" fill="#75d6b2"/>
  <path d="M111 344 L116 350 L126 337" fill="none" stroke="#242424" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="145" y="351" class="body light">video</text>
  <circle cx="376" cy="344" r="13" fill="#75d6b2"/>
  <path d="M369 344 L374 350 L384 337" fill="none" stroke="#242424" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="403" y="351" class="body light">distinct frames</text>
  <circle cx="726" cy="344" r="13" fill="#75d6b2"/>
  <path d="M719 344 L724 350 L734 337" fill="none" stroke="#242424" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="753" y="351" class="body light">transcript</text>
  <circle cx="1014" cy="344" r="13" fill="#75d6b2"/>
  <path d="M1007 344 L1012 350 L1022 337" fill="none" stroke="#242424" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="1041" y="351" class="body light">context.md</text>
  <text x="98" y="401" class="small dim">Complete: runs/VIDEO_ID/bundle/context.md</text>

  <!-- Pack step -->
  <rect x="215" y="486" width="390" height="92" rx="18" fill="#ffd21e" stroke="#242424" stroke-width="3"/>
  <text x="410" y="524" text-anchor="middle" class="caps">OPTIONAL HANDOFF</text>
  <text x="410" y="554" text-anchor="middle" class="mono" fill="#242424">pixi run pack VIDEO_ID</text>
  <path d="M623 532 H762" class="flow"/>

  <rect x="780" y="474" width="440" height="116" rx="20" fill="#d8c7ff" stroke="#242424" stroke-width="3"/>
  <path d="M818 497 H866 L886 517 V566 H818 Z" fill="#ffffff" stroke="#242424" stroke-width="3"/>
  <path d="M866 497 V517 H886" class="thin"/>
  <text x="918" y="526" class="label">yt-decktrace-VIDEO_ID.zip</text>
  <text x="918" y="558" class="small">ready to attach to a multimodal LLM</text>
"""


def render(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    diagrams = {
        "overview.svg": document(
            "yt-decktrace overview",
            "A YouTube video passes through yt-decktrace and becomes distinct frames, timestamped dialogue, context Markdown, and LLM input.",
            610,
            OVERVIEW,
        ),
        "pipeline.svg": document(
            "yt-decktrace processing pipeline",
            "FFmpeg samples the visual track, Pillow and ImageHash retain distinct stable frames, faster-whisper transcribes speech, and both are aligned by timestamp.",
            620,
            PIPELINE,
        ),
        "usage.svg": document(
            "yt-decktrace command usage",
            "A Pixi analyze command produces video, distinct frames, transcript, and context Markdown; an optional pack command creates an LLM-ready ZIP archive.",
            630,
            USAGE,
        ),
    }
    for name, contents in diagrams.items():
        (output_dir / name).write_text(contents, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        default=Path("docs/assets"),
        help="Directory where the SVG files are written",
    )
    args = parser.parse_args()
    render(args.output_dir)


if __name__ == "__main__":
    main()
