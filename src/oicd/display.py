"""Display palette: every color the explorer shows is decided here and served by GET /display.

Neutral reference palette (validated with the dataviz skill's validator, light and dark): no
vendor brand colors. Roles:
- source and dims classes: categorical slots in a fixed order, SYNTHETIC and SCHEMATIC in gray,
  always shown with a text label;
- check status and verdicts: the reserved status colors, always with an icon and a label;
- margins: a diverging map, red (negative) to gray (0 dB) to blue (positive), in 0.4 dB bins
  with a neutral bin of ±ε (the verdict's epsilon), so a margin's color never disagrees with
  its verdict; the map saturates beyond ±2.8 dB;
- wavelength channels: hue by direction (blue for even n, orange for odd n), lightness by channel
  position as a secondary cue; channel identity is carried by labels, never by color alone.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, computed_field

from oicd.provenance import SourceClass
from oicd.registry import EPSILON_DB

_FROZEN = ConfigDict(frozen=True, extra="forbid")

Mode = Literal["light", "dark"]

# Categorical slots 1-6 of the reference palette (light, dark), in the validated order.
_SLOTS = (
    ("#2a78d6", "#3987e5"),  # 1 blue
    ("#eb6834", "#d95926"),  # 2 orange
    ("#1baf7a", "#199e70"),  # 3 aqua
    ("#eda100", "#c98500"),  # 4 yellow
    ("#e87ba4", "#d55181"),  # 5 magenta
    ("#008300", "#008300"),  # 6 green
)
_GRAY = ("#898781", "#898781")

CLASS_ORDER = (
    SourceClass.INFERENCE,
    SourceClass.VENDOR_CLAIM,
    SourceClass.PEER_REVIEWED,
    SourceClass.PUBLISHED_SPEC,
    SourceClass.THIRD_PARTY,
    SourceClass.PROPOSED_STANDARD,
)
CLASS_LABELS = {
    SourceClass.PUBLISHED_SPEC: "Published spec",
    SourceClass.PROPOSED_STANDARD: "Proposed standard",
    SourceClass.VENDOR_CLAIM: "Vendor claim",
    SourceClass.PEER_REVIEWED: "Peer reviewed",
    SourceClass.THIRD_PARTY: "Third party",
    SourceClass.SYNTHETIC: "Synthetic",
    SourceClass.INFERENCE: "Inference",
}
DIMS_LABELS = {
    "PUBLISHED": "Published dimension",
    "VENDOR": "Vendor dimension",
    "INFERENCE": "Inferred dimension",
    "SCHEMATIC": "Schematic",
}
_DIMS_SLOT = {
    "PUBLISHED": SourceClass.PUBLISHED_SPEC,
    "VENDOR": SourceClass.VENDOR_CLAIM,
    "INFERENCE": SourceClass.INFERENCE,
}

# Reserved status colors (mode-invariant), each shown with an icon and a label.
STATUS = {
    "CONSISTENT": ("#0ca30c", "check", "Consistent"),
    "TENSION": ("#fab219", "alert-triangle", "Tension"),
    "CONFLICT": ("#d03b3b", "x-octagon", "Conflict"),
    "NOT_EXCLUDED": ("#0ca30c", "check", "Not excluded"),
    "EXCLUDED": ("#d03b3b", "x-octagon", "Excluded"),
    "NOT_EVALUATED": ("#898781", "minus-circle", "Not evaluated"),
}

# One-hue ramps at matched OKLCH lightness (L 0.76 to 0.43): blue is the reference sequential
# ramp (steps 250 to 600); orange and red were generated at the same lightness levels.
BLUE = ("#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95")
ORANGE = ("#f39776", "#e38968", "#da7550", "#d45e2f", "#c54e1c", "#af4517", "#9c390c", "#883008")
RED = ("#f89189", "#e8827b", "#e06e68", "#da5450", "#ca4442", "#b43b3a", "#a1302f", "#8c2828")
_NEUTRAL = ("#f0efec", "#383835")

MARGIN_RANGE_DB = 3.0  # the color bar spans ±3 dB
MARGIN_STEP_DB = 0.4  # bin width; the eighth bin on each side is open-ended (|M| ≥ 2.8 dB)
CW_COLOR = ("#8f8a7e", "#c9c4b6")  # unmodulated laser supply (wavelength plan not shown)


EDGE_SHADE = 0.62  # feature edges: the face color scaled toward black


def shade(color: str, factor: float) -> str:
    """#rrggbb scaled toward black by factor (0 black, 1 unchanged)."""
    rgb = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(c * factor):02x}" for c in rgb)


class Material(BaseModel):
    """Physically based look of a part material (restrained; no neon outside light paths)."""

    model_config = _FROZEN

    key: str
    label: str
    color: str
    metalness: float
    roughness: float
    transmission: float = 0.0
    opacity: float = 1.0
    ior: float = 1.5

    @computed_field  # type: ignore[prop-decorator]
    @property
    def edge(self) -> str:
        """Feature-edge color: a shade darker than the face."""
        return shade(self.color, EDGE_SHADE)


MATERIALS = (
    Material(key="silicon", label="Silicon", color="#3d4654", metalness=0.15, roughness=0.32),
    Material(
        key="silicon_eic", label="Silicon (EIC)", color="#4a4f5c", metalness=0.2, roughness=0.38
    ),
    Material(
        key="organic_substrate",
        label="Organic substrate",
        color="#565a48",
        metalness=0.0,
        roughness=0.82,
    ),
    Material(
        key="pcb", label="Printed circuit board", color="#2f463c", metalness=0.0, roughness=0.75
    ),
    Material(key="copper", label="Copper", color="#b87333", metalness=1.0, roughness=0.35),
    Material(key="solder", label="Solder (SAC)", color="#c0c2c4", metalness=0.9, roughness=0.4),
    Material(key="steel", label="Stainless steel", color="#9aa1a8", metalness=1.0, roughness=0.45),
    Material(
        key="aluminium", label="Anodized aluminium", color="#b9bdc2", metalness=0.8, roughness=0.5
    ),
    Material(
        key="aluminium_dark",
        label="Black anodized aluminium",
        color="#2f3237",
        metalness=0.7,
        roughness=0.55,
    ),
    Material(
        key="glass",
        label="Glass",
        color="#dfe9ef",
        metalness=0.0,
        roughness=0.05,
        transmission=0.9,
        ior=1.46,
    ),
    Material(key="fiber", label="Fiber (jacketed)", color="#cfcac0", metalness=0.0, roughness=0.6),
    Material(
        key="polymer",
        label="Polymer (ferrules, housings)",
        color="#3a3c40",
        metalness=0.0,
        roughness=0.6,
    ),
    Material(key="rubber", label="Hose (EPDM)", color="#2b2b2b", metalness=0.0, roughness=0.85),
    Material(
        key="oxide",
        label="Silicon dioxide",
        color="#cfd8e3",
        metalness=0.0,
        roughness=0.08,
        transmission=0.6,
        ior=1.45,
    ),
    Material(key="heater", label="Heater (TiN)", color="#b88a4a", metalness=0.8, roughness=0.4),
    Material(key="germanium", label="Germanium", color="#5a5f66", metalness=0.3, roughness=0.4),
    Material(key="doped_p", label="p-doped silicon", color="#7a5a8a", metalness=0.1, roughness=0.4),
    Material(key="doped_n", label="n-doped silicon", color="#4a6a8a", metalness=0.1, roughness=0.4),
    Material(key="hbm", label="Memory stack", color="#2a2c30", metalness=0.2, roughness=0.5),
    Material(
        key="gain", label="Laser gain section", color="#5e4b3c", metalness=0.2, roughness=0.45
    ),
    Material(
        key="outline",
        label="Outline (dimension envelope)",
        color="#9aa0a6",
        metalness=0.0,
        roughness=1.0,
        opacity=0.12,
    ),
)


class Swatch(BaseModel):
    model_config = _FROZEN

    key: str
    label: str
    color: str


class StatusSwatch(BaseModel):
    model_config = _FROZEN

    key: str
    label: str
    color: str
    icon: str


class ColorStop(BaseModel):
    model_config = _FROZEN

    value_db: float
    color: str


class MarginBin(BaseModel):
    """lo_db ≤ M < hi_db; None is unbounded."""

    model_config = _FROZEN

    lo_db: float | None
    hi_db: float | None
    color: str


class ChannelColor(BaseModel):
    model_config = _FROZEN

    channel: int
    direction: Literal["A", "B"]
    color: str


class Palette(BaseModel):
    model_config = _FROZEN

    mode: Mode
    classes: tuple[Swatch, ...]
    dims_classes: tuple[Swatch, ...]
    status: tuple[StatusSwatch, ...]
    margin_scale: tuple[ColorStop, ...]  # color bar ticks
    margin_bins: tuple[MarginBin, ...]  # the map itself: show the bin that holds the value
    margin_range_db: float
    channels: tuple[ChannelColor, ...]
    channel_legend: str
    cw: str  # unmodulated laser supply
    background_top: str  # viewport gradient, neutral
    background_bottom: str
    surface: str
    ink: str
    muted: str
    grid: str
    materials: tuple[Material, ...]
    schematic_tint: str  # the toolbar tint that marks SCHEMATIC parts


def _pick(pair: tuple[str, str], mode: Mode) -> str:
    return pair[0] if mode == "light" else pair[1]


def class_color(cls: SourceClass, mode: Mode = "light") -> str:
    if cls is SourceClass.SYNTHETIC:
        return _pick(_GRAY, mode)
    return _pick(_SLOTS[CLASS_ORDER.index(cls)], mode)


def channel_colors(count: int) -> tuple[ChannelColor, ...]:
    """Even n: direction A, blue ramp; odd n: direction B, orange ramp; lightness by position.
    With one channel per direction, the ramps' middle step."""
    out = []
    per_direction = max((count + 1) // 2, 1)
    for n in range(count):
        ramp = BLUE if n % 2 == 0 else ORANGE
        if per_direction == 1:
            step = 3
        else:
            step = (n // 2) * (len(ramp) - 1) // (per_direction - 1)
        out.append(ChannelColor(channel=n, direction="A" if n % 2 == 0 else "B", color=ramp[step]))
    return tuple(out)


def margin_bins(mode: Mode = "light") -> tuple[MarginBin, ...]:
    """Red bins below −ε (darker with depth), a neutral bin [−ε, ε), blue bins from ε."""
    edges = [k * MARGIN_STEP_DB for k in range(1, 8)]  # 0.4 … 2.8
    red = [MarginBin(lo_db=None, hi_db=-edges[-1], color=RED[7])]
    red += [MarginBin(lo_db=-edges[i], hi_db=-edges[i - 1], color=RED[i]) for i in range(6, 0, -1)]
    red.append(MarginBin(lo_db=-edges[0], hi_db=-EPSILON_DB, color=RED[0]))
    neutral = MarginBin(lo_db=-EPSILON_DB, hi_db=EPSILON_DB, color=_pick(_NEUTRAL, mode))
    blue = [MarginBin(lo_db=EPSILON_DB, hi_db=edges[0], color=BLUE[0])]
    blue += [MarginBin(lo_db=edges[i - 1], hi_db=edges[i], color=BLUE[i]) for i in range(1, 7)]
    blue.append(MarginBin(lo_db=edges[-1], hi_db=None, color=BLUE[7]))
    return (*red, neutral, *blue)


def margin_color(margin_db: float, mode: Mode = "light") -> str:
    """The color of the bin that holds margin_db."""
    for b in margin_bins(mode):
        if (b.lo_db is None or margin_db >= b.lo_db) and (b.hi_db is None or margin_db < b.hi_db):
            return b.color
    raise ValueError(f"margin {margin_db!r} is not a number")


def palette(mode: Mode = "light", channels: int = 16) -> Palette:
    return Palette(
        mode=mode,
        classes=tuple(
            Swatch(key=c.value, label=CLASS_LABELS[c], color=class_color(c, mode))
            for c in (*CLASS_ORDER, SourceClass.SYNTHETIC)
        ),
        dims_classes=tuple(
            Swatch(
                key=k,
                label=DIMS_LABELS[k],
                color=class_color(_DIMS_SLOT[k], mode) if k in _DIMS_SLOT else _pick(_GRAY, mode),
            )
            for k in ("PUBLISHED", "VENDOR", "INFERENCE", "SCHEMATIC")
        ),
        status=tuple(
            StatusSwatch(key=k, label=label, color=color, icon=icon)
            for k, (color, icon, label) in STATUS.items()
        ),
        margin_scale=tuple(
            ColorStop(value_db=v, color=margin_color(v, mode))
            for v in (
                -MARGIN_RANGE_DB,
                -MARGIN_RANGE_DB / 2,
                0.0,
                MARGIN_RANGE_DB / 2,
                MARGIN_RANGE_DB,
            )
        ),
        margin_bins=margin_bins(mode),
        margin_range_db=MARGIN_RANGE_DB,
        channels=channel_colors(channels),
        channel_legend="False color; O-band light is invisible. Hue: direction (blue A, orange B); "
        "shade: channel position; labels give the channel.",
        cw=_pick(CW_COLOR, mode),
        background_top=_pick(("#fbfbfa", "#2a2a28"), mode),
        background_bottom=_pick(("#dedcd5", "#121211"), mode),
        surface=_pick(("#fcfcfb", "#1a1a19"), mode),
        ink=_pick(("#0b0b0b", "#f0efec"), mode),
        muted="#898781",
        grid=_pick(("#e1e0d9", "#2c2c2a"), mode),
        materials=MATERIALS,
        schematic_tint=_pick(("#c3c2b7", "#52514e"), mode),
    )
