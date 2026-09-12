"""Design system partagé entre l'application React et les notebooks d'analyse.

Les tokens sont la transcription littérale des variables CSS (`:root` et `.dark`).
Ils sont exprimés en OKLCH, comme côté front, et convertis en sRGB à la volée afin
qu'une modification du thème React puisse être répliquée ici sans recalcul manuel.
"""

from __future__ import annotations

import math
from typing import Dict, List, Literal, Sequence, Tuple

Mode = Literal["light", "dark"]

# --- Tokens (OKLCH : lightness 0-1, chroma, hue en degrés) ------------------

LIGHT_TOKENS: Dict[str, Tuple[float, float, float]] = {
    "background": (0.9818, 0.0054, 95.0986),
    "foreground": (0.3438, 0.0269, 95.7226),
    "card": (0.9665, 0.0067, 97.3521),
    "card_foreground": (0.1908, 0.0020, 106.5859),
    "popover": (1.0000, 0.0, 0.0),
    "popover_foreground": (0.2671, 0.0196, 98.9390),
    "primary": (0.6171, 0.1375, 39.0427),
    "primary_foreground": (1.0000, 0.0, 0.0),
    "secondary": (0.9245, 0.0138, 92.9892),
    "secondary_foreground": (0.4334, 0.0177, 98.6048),
    "muted": (0.9341, 0.0153, 90.2390),
    "muted_foreground": (0.5341, 0.0078, 97.4503),
    "accent": (0.9245, 0.0138, 92.9892),
    "accent_foreground": (0.2671, 0.0196, 98.9390),
    "destructive": (0.1908, 0.0020, 106.5859),
    "destructive_foreground": (1.0000, 0.0, 0.0),
    "border": (0.8847, 0.0069, 97.3627),
    "input": (0.7621, 0.0156, 98.3528),
    "ring": (0.6171, 0.1375, 39.0427),
    "chart_1": (0.5583, 0.1276, 42.9956),
    "chart_2": (0.6898, 0.1581, 290.4107),
    "chart_3": (0.8816, 0.0276, 93.1280),
    "chart_4": (0.8822, 0.0403, 298.1792),
    "chart_5": (0.5608, 0.1348, 42.0584),
    "sidebar": (0.9663, 0.0080, 98.8792),
}

DARK_TOKENS: Dict[str, Tuple[float, float, float]] = {
    "background": (0.2679, 0.0036, 106.6427),
    "foreground": (0.9576, 0.0027, 106.4494),
    "card": (0.2928, 0.0018, 106.5092),
    "card_foreground": (0.9818, 0.0054, 95.0986),
    "popover": (0.3085, 0.0035, 106.6039),
    "popover_foreground": (0.9211, 0.0040, 106.4781),
    "primary": (0.6724, 0.1308, 38.7559),
    "primary_foreground": (0.1908, 0.0020, 106.5859),
    "secondary": (0.9818, 0.0054, 95.0986),
    "secondary_foreground": (0.3085, 0.0035, 106.6039),
    "muted": (0.2213, 0.0038, 106.7070),
    "muted_foreground": (0.7713, 0.0169, 99.0657),
    "accent": (0.2130, 0.0078, 95.4245),
    "accent_foreground": (0.9663, 0.0080, 98.8792),
    "destructive": (0.6368, 0.2078, 25.3313),
    "destructive_foreground": (1.0000, 0.0, 0.0),
    "border": (0.3618, 0.0101, 106.8928),
    "input": (0.4336, 0.0113, 100.2195),
    "ring": (0.6724, 0.1308, 38.7559),
    "chart_1": (0.5583, 0.1276, 42.9956),
    "chart_2": (0.6898, 0.1581, 290.4107),
    "chart_3": (0.2130, 0.0078, 95.4245),
    "chart_4": (0.3074, 0.0516, 289.3230),
    "chart_5": (0.5608, 0.1348, 42.0584),
    "sidebar": (0.2357, 0.0024, 67.7077),
}

# `--font-sans: Outfit` / `--font-mono: Geist Mono` avec repli sur les polices
# généralement disponibles côté système, matplotlib prenant la première trouvée.
FONT_SANS: List[str] = ["Outfit", "Urbanist", "Poppins", "Noto Sans", "DejaVu Sans"]
FONT_MONO: List[str] = ["Geist Mono", "Ubuntu Mono", "DejaVu Sans Mono"]

# `--radius: 1rem` exprimé en points matplotlib (1rem = 16px, 1px = 0.75pt).
RADIUS_PT: float = 12.0

_CHART_KEYS: Sequence[str] = ("chart_1", "chart_2", "chart_3", "chart_4", "chart_5")

# `--chart-1` à `--chart-5` ne suffisent pas pour des graphiques à nombreuses
# séries : `chart-3`/`chart-4` sont trop clairs et `chart-5` est presque
# indiscernable de `chart-1`. On étend donc le nuancier en restant sur les deux
# teintes de la marque (terracotta ~40°, violet ~290°) et sur le sable ~93°,
# en ne jouant que sur la luminosité et la saturation.
_SERIES_LIGHT: Sequence[Tuple[float, float, float]] = (
    (0.6171, 0.1375, 39.0427),
    (0.6898, 0.1581, 290.4107),
    (0.7000, 0.0700, 93.1280),
    (0.5000, 0.1100, 298.1792),
    (0.4500, 0.1100, 42.0584),
    (0.8200, 0.0600, 93.1280),
    (0.8200, 0.0700, 290.4107),
    (0.3600, 0.0500, 39.0427),
)

_SERIES_DARK: Sequence[Tuple[float, float, float]] = (
    (0.6724, 0.1308, 38.7559),
    (0.7400, 0.1400, 290.4107),
    (0.8300, 0.0600, 93.1280),
    (0.6200, 0.1000, 298.1792),
    (0.5600, 0.1348, 42.0584),
    (0.9000, 0.0400, 93.1280),
    (0.8800, 0.0500, 290.4107),
    (0.4600, 0.0700, 39.0427),
)


# --- Conversion OKLCH -> sRGB ----------------------------------------------


def _srgb_transfer(channel: float) -> float:
    if channel <= 0.0031308:
        return 12.92 * channel
    return 1.055 * channel ** (1 / 2.4) - 0.055


def oklch_to_rgb(lightness: float, chroma: float, hue: float) -> Tuple[float, float, float]:
    """Convertit une couleur OKLCH (hue en degrés) en sRGB normalisé 0-1."""
    hue_rad = math.radians(hue)
    a = chroma * math.cos(hue_rad)
    b = chroma * math.sin(hue_rad)

    l_ = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3

    linear = (
        4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )
    return tuple(min(1.0, max(0.0, _srgb_transfer(max(0.0, channel)))) for channel in linear)


def oklch_to_hex(lightness: float, chroma: float, hue: float) -> str:
    red, green, blue = oklch_to_rgb(lightness, chroma, hue)
    return "#{:02x}{:02x}{:02x}".format(
        round(red * 255), round(green * 255), round(blue * 255)
    )


def colors(mode: Mode = "light") -> Dict[str, str]:
    """Retourne les tokens du thème demandé sous forme de codes hexadécimaux."""
    tokens = DARK_TOKENS if mode == "dark" else LIGHT_TOKENS
    return {name: oklch_to_hex(*value) for name, value in tokens.items()}


def palette(mode: Mode = "light") -> List[str]:
    """Couleurs de graphiques telles que définies côté front (`--chart-1` à `--chart-5`)."""
    theme = colors(mode)
    return [theme[key] for key in _CHART_KEYS]


def series_palette(mode: Mode = "light") -> List[str]:
    """Nuancier étendu, lisible sur fond `card`, pour les graphiques multi-séries."""
    tokens = _SERIES_DARK if mode == "dark" else _SERIES_LIGHT
    return [oklch_to_hex(*token) for token in tokens]


def sequential_cmap(mode: Mode = "light", name: str = "pmu_sequential"):
    """Dégradé continu allant du `muted` au `primary`, pour heatmaps et densités."""
    from matplotlib.colors import LinearSegmentedColormap

    theme = colors(mode)
    stops = [theme["background"], theme["chart_3"], theme["primary"], theme["chart_1"]]
    if mode == "dark":
        stops = [theme["card"], theme["accent"], theme["primary"], theme["chart_5"]]
    return LinearSegmentedColormap.from_list(name, stops)


def diverging_cmap(mode: Mode = "light", name: str = "pmu_diverging"):
    """Dégradé `chart-2` (violet) -> neutre -> `chart-1` (terracotta)."""
    from matplotlib.colors import LinearSegmentedColormap

    theme = colors(mode)
    return LinearSegmentedColormap.from_list(
        name, [theme["chart_2"], theme["chart_4"], theme["background"], theme["chart_3"], theme["chart_1"]]
    )


def apply_theme(mode: Mode = "light", *, figsize: Tuple[float, float] = (11.0, 5.0)) -> Dict[str, str]:
    """Applique le design system aux rcParams matplotlib et retourne les tokens."""
    import matplotlib as mpl
    from cycler import cycler

    theme = colors(mode)
    mpl.rcParams.update(
        {
            "figure.figsize": figsize,
            "figure.dpi": 110,
            "figure.facecolor": theme["background"],
            "figure.edgecolor": theme["background"],
            "figure.titlesize": 15,
            "figure.titleweight": "bold",
            "savefig.facecolor": theme["background"],
            "savefig.bbox": "tight",
            "axes.facecolor": theme["card"],
            "axes.edgecolor": theme["border"],
            "axes.labelcolor": theme["muted_foreground"],
            "axes.titlecolor": theme["foreground"],
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.titlepad": 12,
            "axes.labelsize": 10,
            "axes.labelpad": 8,
            "axes.linewidth": 0.8,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "axes.axisbelow": True,
            "axes.unicode_minus": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.prop_cycle": cycler(color=series_palette(mode)),
            "grid.color": theme["border"],
            "grid.linewidth": 0.8,
            "grid.alpha": 0.9,
            "text.color": theme["foreground"],
            "font.family": "sans-serif",
            "font.sans-serif": FONT_SANS,
            "font.monospace": FONT_MONO,
            "font.size": 10,
            "xtick.color": theme["muted_foreground"],
            "ytick.color": theme["muted_foreground"],
            "xtick.labelcolor": theme["muted_foreground"],
            "ytick.labelcolor": theme["muted_foreground"],
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "xtick.major.size": 0,
            "ytick.major.size": 0,
            "legend.frameon": False,
            "legend.fontsize": 9,
            "legend.labelcolor": theme["foreground"],
            "lines.linewidth": 2.0,
            "lines.solid_capstyle": "round",
            "lines.markersize": 5,
            "patch.linewidth": 0,
            "patch.edgecolor": theme["card"],
            "boxplot.patchartist": True,
            "hist.bins": 40,
        }
    )
    return theme


_ROUNDED_LABEL = "_pmu_rounded_bar"


def _rounded_bar_path(bbox, radius_x: float, radius_y: float, orientation: str):
    """Construit le contour d'une barre dont seule l'extrémité libre est arrondie."""
    from matplotlib.path import Path

    x0, y0, x1, y1 = bbox.xmin, bbox.ymin, bbox.xmax, bbox.ymax
    if orientation == "vertical":
        radius_x = min(radius_x, (x1 - x0) / 2)
        radius_y = min(radius_y, y1 - y0)
        vertices = [
            (x0, y0),
            (x0, y1 - radius_y),
            (x0, y1),
            (x0 + radius_x, y1),
            (x1 - radius_x, y1),
            (x1, y1),
            (x1, y1 - radius_y),
            (x1, y0),
            (x0, y0),
        ]
    else:
        radius_y = min(radius_y, (y1 - y0) / 2)
        radius_x = min(radius_x, x1 - x0)
        vertices = [
            (x0, y0),
            (x1 - radius_x, y0),
            (x1, y0),
            (x1, y0 + radius_y),
            (x1, y1 - radius_y),
            (x1, y1),
            (x1 - radius_x, y1),
            (x0, y1),
            (x0, y0),
        ]
    codes = [
        Path.MOVETO,
        Path.LINETO,
        Path.CURVE3,
        Path.CURVE3,
        Path.LINETO,
        Path.CURVE3,
        Path.CURVE3,
        Path.LINETO,
        Path.CLOSEPOLY,
    ]
    return Path(vertices, codes)


def rounded_bars(ax, radius_pt: float = RADIUS_PT / 2, orientation: str = "vertical") -> None:
    """Arrondit l'extrémité des barres, à l'image du `--radius` du design system.

    Le rayon est exprimé en points puis converti en unités de données juste avant
    le rendu : il reste donc constant à l'écran quelles que soient les échelles.
    """
    from matplotlib.patches import PathPatch, Rectangle

    bars = [
        patch
        for patch in ax.patches
        if isinstance(patch, Rectangle)
        and patch.get_visible()
        and patch.get_label() != _ROUNDED_LABEL
    ]
    if not bars:
        return

    replacements = []
    for bar in bars:
        rounded = PathPatch(
            _rounded_bar_path(bar.get_bbox(), 0.0, 0.0, orientation),
            facecolor=bar.get_facecolor(),
            edgecolor="none",
            alpha=bar.get_alpha(),
            hatch=bar.get_hatch(),
            zorder=bar.get_zorder(),
            label=_ROUNDED_LABEL,
        )
        bar.set_visible(False)
        ax.add_patch(rounded)
        replacements.append((bar, rounded))

    def refresh_paths(renderer=None) -> None:
        transform = ax.transData
        origin = transform.transform((0.0, 0.0))
        pixels_per_x = abs(transform.transform((1.0, 0.0))[0] - origin[0]) or 1.0
        pixels_per_y = abs(transform.transform((0.0, 1.0))[1] - origin[1]) or 1.0
        radius_px = radius_pt * ax.figure.dpi / 72.0
        for source, target in replacements:
            target.set_path(
                _rounded_bar_path(
                    source.get_bbox(),
                    radius_px / pixels_per_x,
                    radius_px / pixels_per_y,
                    orientation,
                )
            )

    original_draw = ax.draw

    def draw(renderer, *args, **kwargs):
        refresh_paths(renderer)
        return original_draw(renderer, *args, **kwargs)

    refresh_paths()
    ax.draw = draw


def annotate_bars(
    ax,
    *,
    fmt: str = "{:,.0f}",
    orientation: str = "vertical",
    padding: float = 0.01,
    color: str | None = None,
) -> None:
    """Ajoute les valeurs au bout des barres, en typographie secondaire."""
    from matplotlib.patches import Rectangle

    label_color = color or ax.yaxis.label.get_color()
    is_vertical = orientation == "vertical"
    rectangles = [patch for patch in ax.patches if isinstance(patch, Rectangle)]
    if not rectangles:
        return

    span = (
        max(abs(rect.get_height()) for rect in rectangles)
        if is_vertical
        else max(abs(rect.get_width()) for rect in rectangles)
    )
    offset = span * padding

    for rect in rectangles:
        if is_vertical:
            value = rect.get_height()
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                value + offset,
                fmt.format(value),
                ha="center",
                va="bottom",
                fontsize=8,
                color=label_color,
            )
        else:
            value = rect.get_width()
            ax.text(
                value + offset,
                rect.get_y() + rect.get_height() / 2,
                fmt.format(value),
                ha="left",
                va="center",
                fontsize=8,
                color=label_color,
            )


def color_cycle(count: int, mode: Mode = "light") -> List[str]:
    """Étend le nuancier à `count` séries en le répétant si besoin."""
    base = series_palette(mode)
    return [base[index % len(base)] for index in range(count)]


def table_css(mode: Mode = "light") -> List[Dict[str, object]]:
    """Feuille de style des tableaux, calquée sur les cartes du front.

    Destinée à `pandas.io.formats.style.Styler.set_table_styles`.
    """
    theme = colors(mode)
    famille = ", ".join(f'"{police}"' for police in FONT_SANS) + ", sans-serif"
    bordure = f"1px solid {theme['border']}"
    return [
        {
            "selector": "",
            "props": [
                ("border-collapse", "separate"),
                ("border-spacing", "0"),
                ("border", bordure),
                ("border-radius", "12px"),
                ("overflow", "hidden"),
                ("font-family", famille),
                ("font-size", "13px"),
                ("color", theme["foreground"]),
                ("background-color", theme["card"]),
                ("margin", "4px 0 14px 0"),
            ],
        },
        {
            "selector": "caption",
            "props": [
                ("caption-side", "top"),
                ("text-align", "left"),
                ("font-size", "14px"),
                ("font-weight", "600"),
                ("padding", "2px 2px 10px 2px"),
                ("color", theme["foreground"]),
            ],
        },
        {
            "selector": "thead th",
            "props": [
                ("background-color", theme["secondary"]),
                ("color", theme["muted_foreground"]),
                ("font-weight", "600"),
                ("font-size", "10.5px"),
                ("letter-spacing", "0.05em"),
                ("text-transform", "uppercase"),
                ("text-align", "right"),
                ("padding", "9px 14px"),
                ("border-bottom", bordure),
            ],
        },
        {
            "selector": "thead th.blank, thead th.index_name",
            "props": [("text-align", "left"), ("background-color", theme["secondary"])],
        },
        {
            "selector": "tbody th",
            "props": [
                ("text-align", "left"),
                ("font-weight", "500"),
                ("padding", "8px 14px"),
                ("color", theme["foreground"]),
                ("border-bottom", bordure),
            ],
        },
        {
            "selector": "tbody td",
            "props": [
                ("text-align", "right"),
                ("padding", "8px 14px"),
                ("border-bottom", bordure),
                ("font-variant-numeric", "tabular-nums"),
            ],
        },
        {
            "selector": "tbody tr:nth-child(even) th, tbody tr:nth-child(even) td",
            "props": [("background-color", theme["background"])],
        },
        {
            "selector": "tbody tr:last-child th, tbody tr:last-child td",
            "props": [("border-bottom", "none")],
        },
    ]
