"""Draw the research warning into the picture, not only beside it."""

from __future__ import annotations

RESEARCH_LABEL = "RESEARCH SAMPLE: single word. Not a patient message. Not reviewed."
CITATION = (
    "Maina E., Wanzare L., Obuhuma J., Ayere M., Kang'ahi M., Okutoyi J. "
    "Kenyan sign language word-based pose dataset. Data in Brief 60:111502 (2025). "
    "doi:10.1016/j.dib.2025.111502. Data: Zenodo, doi:10.5281/zenodo.14974973."
)
BANNER = (122, 31, 31)


def stamp_banner(width: int = 8, height: int = 4) -> list[tuple[int, int, int]]:
    """A solid banner. A screenshot of the frame still carries this block."""
    return [BANNER for _ in range(width * height)]


def frame_svg(sticks: list[tuple[float, float, float, float]], label: str = RESEARCH_LABEL) -> str:
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">',
        '<rect id="research-banner" x="0" y="0" width="640" height="48" fill="#7a1f1f"/>',
        f'<text id="research-label" x="12" y="30" fill="#ffffff" font-size="14">{label}</text>',
    ]
    for x1, y1, x2, y2 in sticks:
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            'stroke="#102027" stroke-width="3"/>'
        )
    lines.append(f'<text x="12" y="348" fill="#334047" font-size="10">{CITATION}</text>')
    lines.append("</svg>")
    return "".join(lines)
