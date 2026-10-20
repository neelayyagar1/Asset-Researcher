"""Charts, as inline SVG.

These were matplotlib figures rendered to PNG. SVG replaces that for four
reasons that all matter to how the page reads:

1. **The chart inherits the page's typefaces.** A rasterised chart carries
   whatever font the plotting library found on the host, so the same report
   rendered on a laptop and on a Linux container showed two different faces
   for the axis labels. Text in SVG is text.
2. **It stays sharp.** A PNG at any fixed resolution is soft on a retina
   display and blurred when a reader zooms to check a figure.
3. **No grey rectangle.** A rasterised chart carries its own background and
   sits on the page as a visible pasted tile.
4. **No matplotlib.** Dropping it removes the project's heaviest dependency
   and the only one needing a display-server workaround.

Conventions, unchanged from the matplotlib version because they are about
reading rather than drawing:

- One axis per chart. Revenue and margin are two charts, never two scales on
  one. A dual-axis chart lets the author choose where the lines cross.
- The subject is the only coloured mark in a peer chart. Colour follows the
  entity, not its rank, so filtering peers never repaints the survivors.
- Direct labels, selectively. A number on every point is noise.
- Horizontal gridlines only, recessive, behind the marks. No frame.
"""

from __future__ import annotations

from html import escape

from asset_researcher.quant.comps import CompsTable
from asset_researcher.quant.series import MetricSeries
from asset_researcher.quant.valuation import DcfInputs, DcfResult, ValuationCase
from asset_researcher.ui import theme

# Pegged to the page's type scale rather than chosen per chart, so a size
# inside an SVG is the same size beside it. Every chart is drawn at the
# pixel width it will occupy, so a user unit is a pixel.
_LABEL = theme.CHART_LABEL_PX
_TICK = theme.CHART_TICK_PX
_TITLE = theme.CHART_TITLE_PX
# One step below the tick size, for a series name or a key sitting beside
# the figure it names. Declared here because seven ad-hoc sizes inside a
# 1.4px band had grown back inside this file, which is the same pathology
# the page's type scale was built to end.
_FINE = theme.CHART_FINE_PX

# The normalisation window quant/valuation.py uses for its base figure.
# The chart draws the same one so the rule and the model agree.
_BASE_WINDOW = 3

_MONO = theme.FONT_MONO
_SANS = theme.FONT_SANS
# Chart titles are set in the display face, which ties them to the
# masthead rather than letting each figure float free of the page.
_DISPLAY = theme.FONT_DISPLAY


def _text(
    x: float,
    y: float,
    body: str,
    size: float = _LABEL,
    fill: str = theme.INK,
    anchor: str = "start",
    weight: str = "400",
    font: str = _MONO,
    opacity: float = 1.0,
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" '
        f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
        f'font-weight="{weight}" opacity="{opacity}" '
        f'style="font-variant-numeric:tabular-nums">{escape(body)}</text>'
    )


def _describe(what: str, rows: list[tuple[str, str]]) -> str:
    """A chart's data as a sentence, for a reader who is not looking at it.

    An accessible name alone says a chart exists. This says what is in it,
    which is the part that was missing: none of these graphics conveyed
    their data non-visually by any route.
    """
    if not rows:
        return what
    body = "; ".join(f"{k} {v}" for k, v in rows if v)
    return f"{what}. {body}." if body else what


def _multiple_text(value: float | None) -> str:
    return f"{value:,.1f}x" if value is not None else "not meaningful"


def _frame(
    width: float, height: float, body: str, label: str = "", describe: str = ""
) -> str:
    """Scalable, but never beyond the width it was laid out for.

    Without the cap a chart stretched to a wider container scales its type
    with it, so the same 12.5px title renders at 22px in the export and at
    12.5px on the page. Capping at the design width keeps a type size in a
    chart equal to a type size on the page it sits on.
    """
    # `role="img"` with no name is an unlabelled image, and every chart
    # here was one: no aria-label, no <title>, no <desc>. A reader not
    # looking at the picture was told nothing at all. The title names the
    # chart and the description says what it shows; where a caller gives
    # neither, the graphic is marked presentational instead, which is
    # honest rather than announcing an unnamed image.
    if not label:
        return (
            f'<svg viewBox="0 0 {width:.0f} {height:.0f}" '
            f'style="max-width:{width:.0f}px" aria-hidden="true" '
            f'xmlns="http://www.w3.org/2000/svg" role="presentation">'
            f"{body}</svg>"
        )
    desc = f"<desc>{escape(describe)}</desc>" if describe else ""
    return (
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" '
        f'style="max-width:{width:.0f}px" '
        f'xmlns="http://www.w3.org/2000/svg" role="img">'
        f"<title>{escape(label)}</title>{desc}{body}</svg>"
    )


def figure(svg: str | None, caption: str = "") -> str:
    """Wrap a chart with its caption, or return nothing if there is no chart."""
    if not svg:
        return ""
    foot = f"<figcaption>{escape(caption)}</figcaption>" if caption else ""
    return f'<figure class="ar-figure">{svg}{foot}</figure>'


def _title_block(x: float, title: str, subtitle: str) -> str:
    out = _text(x, 13, title, _TITLE, theme.INK, weight="500", font=_DISPLAY)
    if subtitle:
        out += _text(x, 27, subtitle, _TICK, theme.INK_MUTED, font=_SANS)
    return out


def _axis_top(maximum: float, step: float) -> float:
    """The first gridline at or above the data.

    `(int(maximum / step) + 1) * step` always adds a whole step, even when
    the maximum already sits on one. Apple's revenue peaks at $416B against
    a $100B step, so the axis ran to $600B and spent 44% of the plot on
    nothing, which flattens the trend the chart exists to show.
    """
    if maximum <= 0:
        return step
    steps = maximum / step
    # A small cushion so a direct label above the tallest bar has room.
    return (int(steps) + 1) * step if steps > int(steps) * 1.001 else maximum


def _nice_step(span: float, target: int = 4) -> float:
    """A round gridline interval near `span / target`.

    Axis labels at 1, 2, 2.5 or 5 times a power of ten are the ones a reader
    can do arithmetic against; 0.37 intervals are not.
    """
    if span <= 0:
        return 1.0
    raw = span / max(target, 1)
    magnitude = 10 ** _floor_log10(raw)
    for multiple in (1, 2, 2.5, 5, 10):
        if raw <= multiple * magnitude:
            return multiple * magnitude
    return 10 * magnitude


def _floor_log10(value: float) -> int:
    exponent = 0
    while value >= 10:
        value /= 10
        exponent += 1
    while value < 1:
        value *= 10
        exponent -= 1
    return exponent


def _money(value: float) -> str:
    magnitude = abs(value)
    if magnitude >= 1e9:
        return f"${value / 1e9:,.0f}B"
    if magnitude >= 1e6:
        return f"${value / 1e6:,.0f}M"
    if magnitude >= 1e3:
        return f"${value / 1e3:,.0f}K"
    return f"${value:,.0f}"


def _money_precise(value: float) -> str:
    """One decimal, negatives in parentheses.

    The published convention, and the one the projection table already used.
    A bridge printing "$-68.0B" next to a table printing "($68.0B)" for the
    same figure undermines both.
    """
    if value < 0:
        return f"({_money_precise(abs(value))})"
    if value >= 1e9:
        return f"${value / 1e9:,.1f}B"
    if value >= 1e6:
        return f"${value / 1e6:,.1f}M"
    return f"${value:,.0f}"


def _points(series: MetricSeries, metric: str):
    return series.series.get(metric) or []


# --------------------------------------------------------- filed trends


def metric_bars(
    series: MetricSeries,
    metric: str,
    title: str,
    subtitle: str = "",
    width: float = 548,
    height: float = 232,
) -> str | None:
    """One filed metric by period, as bars with the value on each mark."""
    points = _points(series, metric)
    if len(points) < 2:
        return None

    labels = [p.frame_label for p in points]
    values = [p.value for p in points]

    pad_l, pad_r, pad_t, pad_b = 52.0, 10.0, 42.0, 26.0
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    top = max(max(values), 0.0)
    bottom = min(min(values), 0.0)
    step = _nice_step(top - bottom)
    axis_top = _axis_top(top, step) if top else step
    # Mirrors _axis_top: the old form subtracted a whole extra step below
    # the minimum whenever any value was negative, wasting a full band and
    # pushing the zero line up the plot.
    axis_bottom = -_axis_top(-bottom, step) if bottom < 0 else 0.0
    span = axis_top - axis_bottom or 1.0

    def y_of(value: float) -> float:
        return pad_t + plot_h - (value - axis_bottom) / span * plot_h

    body = [_title_block(0, title, subtitle)]

    tick = axis_bottom
    while tick <= axis_top + step / 2:
        y = y_of(tick)
        # The zero line is drawn darker than the other gridlines: it is the
        # baseline a reader measures a bar against, not another increment.
        body.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" '
            f'stroke="{theme.INK_MUTED if tick == 0 else theme.RULE}" '
            f'stroke-width="1"/>'
        )
        body.append(
            _text(pad_l - 8, y + 3.2, _money(tick), _TICK, theme.INK_MUTED, "end")
        )
        tick += step

    slot = plot_w / len(values)
    bar_w = min(slot * 0.56, 44.0)
    zero_y = y_of(0.0)

    for index, (label, value) in enumerate(zip(labels, values)):
        centre = pad_l + slot * (index + 0.5)
        y = y_of(value)
        top_y, bar_h = (y, zero_y - y) if value >= 0 else (zero_y, y - zero_y)
        body.append(
            f'<rect x="{centre - bar_w / 2:.1f}" y="{top_y:.1f}" '
            f'width="{bar_w:.1f}" height="{max(bar_h, 0.6):.1f}" '
            f'fill="{theme.ACCENT}"/>'
        )
        body.append(
            _text(
                centre,
                (y - 6) if value >= 0 else (y + 12),
                _money_precise(value),
                _LABEL,
                theme.INK,
                "middle",
                weight="500",
            )
        )
        body.append(
            _text(centre, height - 8, label, _TICK, theme.INK_MUTED, "middle")
        )

    return _frame(
        width, height, "".join(body),
        label=title,
        describe=_describe(
            subtitle or title,
            [(p.frame_label, _money_precise(p.value)) for p in points],
        ),
    )


def margin_lines(
    series: MetricSeries, width: float = 548, height: float = 232
) -> str | None:
    """Gross and operating margin on one percentage scale.

    Both are percentages of the same denominator, which is the only
    condition under which two measures belong on a single axis.
    """
    revenue = {p.frame_label: p.value for p in _points(series, "revenue")}
    if len(revenue) < 2:
        return None

    lines = []
    for metric, label, colour in (
        ("gross_profit", "Gross margin", theme.ACCENT),
        ("operating_income", "Operating margin", theme.ACCENT_2),
    ):
        pairs = [
            (p.frame_label, p.value / revenue[p.frame_label] * 100)
            for p in _points(series, metric)
            if revenue.get(p.frame_label)
        ]
        if len(pairs) >= 2:
            lines.append((label, colour, pairs))
    if not lines:
        return None

    periods = [p.frame_label for p in _points(series, "revenue")]
    all_values = [v for _, _, pairs in lines for _, v in pairs]

    pad_l, pad_r, pad_t, pad_b = 46.0, 74.0, 42.0, 26.0
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    step = _nice_step(max(all_values) - min(all_values), 3)
    axis_top = _axis_top(max(all_values), step)
    axis_bottom = max(0.0, (int(min(all_values) / step) - 1) * step)
    span = axis_top - axis_bottom or 1.0

    def y_of(value: float) -> float:
        return pad_t + plot_h - (value - axis_bottom) / span * plot_h

    def x_of(period: str) -> float:
        index = periods.index(period)
        divisor = max(len(periods) - 1, 1)
        return pad_l + plot_w * index / divisor

    body = [_title_block(0, "Margin trend", "Percentage of revenue, as filed")]

    tick = axis_bottom
    while tick <= axis_top + step / 2:
        y = y_of(tick)
        body.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" '
            f'y2="{y:.1f}" stroke="{theme.RULE}" stroke-width="1"/>'
        )
        body.append(
            _text(pad_l - 8, y + 3.2, f"{tick:,.0f}%", _TICK, theme.INK_MUTED, "end")
        )
        tick += step

    for period in periods:
        body.append(
            _text(x_of(period), height - 8, period, _TICK, theme.INK_MUTED, "middle")
        )

    for label, colour, pairs in lines:
        path = " ".join(
            f"{'M' if i == 0 else 'L'}{x_of(p):.1f},{y_of(v):.1f}"
            for i, (p, v) in enumerate(pairs)
        )
        body.append(
            f'<path d="{path}" fill="none" stroke="{colour}" '
            f'stroke-width="1.9" stroke-linejoin="round"/>'
        )
        for period, value in pairs:
            body.append(
                f'<circle cx="{x_of(period):.1f}" cy="{y_of(value):.1f}" '
                f'r="2.9" fill="{theme.SURFACE}" stroke="{colour}" '
                f'stroke-width="1.6"/>'
            )
        # Label the series at its last point, which doubles as the legend.
        last_period, last_value = pairs[-1]
        body.append(
            _text(
                x_of(last_period) + 9,
                y_of(last_value) - 3,
                f"{last_value:,.1f}%",
                _LABEL,
                colour,
                weight="500",
            )
        )
        body.append(
            _text(
                x_of(last_period) + 9,
                y_of(last_value) + 8,
                label,
                _FINE,
                theme.INK_MUTED,
                font=_SANS,
            )
        )

    return _frame(
        width, height, "".join(body),
        label="Gross and operating margin by filed year",
        describe=_describe(
            "Both margins as a percentage of revenue",
            [
                (f"{name} {period}", f"{value:,.1f}%")
                for name, _, pairs in lines
                for period, value in pairs
            ],
        ),
    )


# ------------------------------------------------------------ peer context


def peer_bars(
    table: CompsTable, attribute: str, title: str, width: float = 548
) -> str | None:
    """Where the subject sits against its peer set on one multiple.

    Peers are grey and the subject is the single coloured bar, so the eye
    lands on the comparison. Extreme multiples are excluded: a 1,218x
    trailing P/E compresses every other bar to nothing and says only that a
    denominator collapsed.
    """
    if table is None or not table.rows:
        return None

    entries = [
        (row.ticker, value, row.is_subject)
        for row in table.rows
        if (value := getattr(row, attribute, None)) is not None
        and not (row.outlier_multiples and not row.is_subject)
    ]
    if len(entries) < 3:
        return None

    entries.sort(key=lambda e: e[1])

    pad_l, pad_r, pad_t, pad_b = 44.0, 54.0, 42.0, 22.0
    row_h = 21.0
    height = pad_t + pad_b + row_h * len(entries)
    plot_w = width - pad_l - pad_r

    ceiling = max(v for _, v, _ in entries) * 1.06 or 1.0
    body = [
        _title_block(0, title, "Subject highlighted, extreme multiples excluded")
    ]

    median = table.median(attribute)
    if median is not None and median <= ceiling:
        x = pad_l + plot_w * median / ceiling
        body.append(
            f'<line x1="{x:.1f}" y1="{pad_t - 4:.1f}" x2="{x:.1f}" '
            f'y2="{height - pad_b + 2:.1f}" stroke="{theme.INK_MUTED}" '
            f'stroke-width="1" stroke-dasharray="3 3"/>'
        )
        body.append(
            _text(
                x,
                height - 7,
                f"Peer median {median:,.1f}x",
                _FINE,
                theme.INK_MUTED,
                "middle",
                font=_SANS,
            )
        )

    for index, (ticker, value, is_subject) in enumerate(entries):
        y = pad_t + row_h * index
        bar_h = row_h * 0.6
        bar_w = max(plot_w * value / ceiling, 1.0)
        colour = theme.ACCENT if is_subject else theme.NEUTRAL
        body.append(
            f'<rect x="{pad_l}" y="{y:.1f}" width="{bar_w:.1f}" '
            f'height="{bar_h:.1f}" fill="{colour}"/>'
        )
        body.append(
            _text(
                pad_l - 8,
                y + bar_h - 2.6,
                ticker,
                _TICK,
                theme.INK if is_subject else theme.INK_MUTED,
                "end",
                weight="500" if is_subject else "400",
            )
        )
        body.append(
            _text(
                pad_l + bar_w + 6,
                y + bar_h - 2.6,
                f"{value:,.1f}x",
                _LABEL,
                theme.INK if is_subject else theme.INK_MUTED,
                weight="500" if is_subject else "400",
            )
        )

    return _frame(
        width, height, "".join(body),
        label=f"{title}: the subject against its peer set",
        describe=_describe(
            f"{title} for each company in the peer set",
            [
                (f"{ticker} (subject)" if subject else ticker,
                 _multiple_text(value))
                for ticker, value, subject in entries
            ],
        ),
    )


# -------------------------------------------------------------- valuation


def valuation_range(
    cases: list[ValuationCase],
    market_price: float | None,
    width: float = 548,
    height: float = 200,
) -> str | None:
    """Bear, base and bull against the traded price.

    The spread is the analysis; a single point estimate hides it. The traded
    price is drawn as a rule rather than a fourth marker, because it is the
    benchmark the cases are read against rather than another case.
    """
    if not cases or not market_price:
        return None

    values = [c.value_per_share for c in cases]
    high = max(max(values), market_price)

    # A real scale anchored at zero, not a window fitted to the data. The
    # axis used to be the data range plus 16% at each end, which means a
    # three-fold spread and a five-percent spread drew identically: the one
    # chart whose stated purpose is that the spread is the analysis was the
    # one chart that could not show a spread.
    step = _nice_step(high, 4)
    axis_low, axis_high = 0.0, _axis_top(high, step)
    span = axis_high - axis_low or 1.0

    pad_l, pad_r = 18.0, 18.0
    plot_w = width - pad_l - pad_r
    axis_y = 108.0

    def x_of(value: float) -> float:
        return pad_l + (value - axis_low) / span * plot_w

    body = [
        _title_block(
            0,
            "Modelled value per share against traded price",
            "Each case is a full model run at the stated assumptions",
        )
    ]

    # Gridlines and ticks, so the spread can be measured rather than
    # inferred from where the marks happen to sit.
    tick = 0.0
    while tick <= axis_high + step / 2:
        x = x_of(tick)
        body.append(
            f'<line x1="{x:.1f}" y1="{axis_y - 30:.1f}" x2="{x:.1f}" '
            f'y2="{axis_y + 18:.1f}" stroke="{theme.RULE}" stroke-width="1"/>'
        )
        body.append(
            _text(x, axis_y + 30, f"${tick:,.0f}", _TICK, theme.INK_MUTED,
                  "middle")
        )
        tick += step

    # The band spanning bear to bull, with the cases marked on it.
    body.append(
        f'<line x1="{x_of(min(values)):.1f}" y1="{axis_y}" '
        f'x2="{x_of(max(values)):.1f}" y2="{axis_y}" '
        # Full opacity: at 0.4 this composited to 1.54:1, so the band
        # that states the whole valuation range was the least visible
        # thing in the chart.
        f'stroke="{theme.NEUTRAL}" stroke-width="7" '
        f'stroke-linecap="butt"/>'
    )

    for case in sorted(cases, key=lambda c: c.value_per_share):
        x = x_of(case.value_per_share)
        # A tick, not a filled dot. A dot on a track is a slider, which is a
        # control, and nothing on this scale is draggable.
        body.append(
            f'<line x1="{x:.1f}" y1="{axis_y - 7:.1f}" x2="{x:.1f}" '
            f'y2="{axis_y + 7:.1f}" stroke="{theme.ACCENT}" '
            f'stroke-width="2.5"/>'
        )
        body.append(
            _text(x, axis_y - 26, case.name, _TICK, theme.INK_MUTED, "middle",
                  font=_SANS)
        )
        body.append(
            _text(
                x,
                axis_y - 13,
                f"${case.value_per_share:,.0f}",
                _LABEL,
                theme.INK,
                "middle",
                weight="500",
            )
        )

    price_x = x_of(market_price)
    body.append(
        f'<line x1="{price_x:.1f}" y1="{axis_y - 40:.1f}" x2="{price_x:.1f}" '
        f'y2="{axis_y + 20:.1f}" stroke="{theme.ACCENT_2}" stroke-width="1.8"/>'
    )
    # Anchored away from the rule and flipped near the right edge so the
    # label is never printed over the line it describes.
    on_right = price_x > width * 0.72
    body.append(
        _text(
            price_x + (-8 if on_right else 8),
            axis_y + 46,
            f"Traded ${market_price:,.2f}",
            _LABEL,
            theme.ACCENT_2,
            "end" if on_right else "start",
            weight="500",
        )
    )

    return _frame(
        width, height, "".join(body),
        label="Valuation range against the traded price",
        describe=_describe(
            "Each modelled case, and the traded price as a rule",
            [(c.name, f"${c.value_per_share:,.2f}") for c in cases]
            + (
                [("Traded price", f"${market_price:,.2f}")]
                if market_price
                else []
            ),
        ),
    )


def dcf_bridge(
    dcf: DcfResult, inputs: DcfInputs, width: float = 548, height: float = 236
) -> str | None:
    """Forecast cash flows, terminal value, net debt, equity value.

    The bridge every published model carries. It answers in one glance the
    question the single output cannot: how much of this valuation is the
    forecast and how much is the perpetuity assumption sitting behind it.
    """
    if dcf is None or inputs is None:
        return None

    # The bridge step is minus net debt, so a net-cash filer adds here. It
    # was labelled "Net debt $33.8B" on a company holding net cash, which
    # reads as debt being added to enterprise value and is nonsense.
    bridge_step = -inputs.net_debt
    bridge_label = "Less net debt" if bridge_step < 0 else "Plus net cash"

    bars = [
        ("PV forecast", dcf.pv_forecast, theme.ACCENT, False),
        ("PV terminal", dcf.pv_terminal, theme.NEUTRAL, False),
        ("Enterprise value", dcf.enterprise_value, theme.ACCENT, True),
        (bridge_label, bridge_step, theme.ACCENT_2, False),
        ("Equity value", dcf.equity_value, theme.ACCENT, True),
    ]

    pad_l, pad_r, pad_t, pad_b = 54.0, 10.0, 44.0, 30.0
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    # Running cumulative positions, so the increments stack the way a
    # waterfall reads, with the two totals drawn from the baseline.
    running = 0.0
    geometry = []
    for label, value, colour, is_total in bars:
        if is_total:
            start, end = 0.0, value
            running = value
        else:
            start, end = running, running + value
            running = end
        geometry.append((label, value, colour, is_total, start, end))

    extremes = [v for _, _, _, _, s, e in geometry for v in (s, e)] + [0.0]
    step = _nice_step(max(extremes) - min(extremes))
    axis_top = _axis_top(max(extremes), step)
    axis_bottom = min(0.0, (int(min(extremes) / step)) * step)
    span = axis_top - axis_bottom or 1.0

    def y_of(value: float) -> float:
        return pad_t + plot_h - (value - axis_bottom) / span * plot_h

    body = [
        _title_block(
            0,
            "Valuation bridge",
            "Forecast and terminal value to equity value, computed",
        )
    ]

    tick = axis_bottom
    while tick <= axis_top + step / 2:
        y = y_of(tick)
        body.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" '
            f'y2="{y:.1f}" stroke="{theme.RULE}" stroke-width="1"/>'
        )
        body.append(
            _text(pad_l - 8, y + 3.2, _money(tick), _TICK, theme.INK_MUTED, "end")
        )
        tick += step

    slot = plot_w / len(geometry)
    bar_w = min(slot * 0.52, 46.0)

    for index, (label, value, colour, is_total, start, end) in enumerate(geometry):
        centre = pad_l + slot * (index + 0.5)
        top_y = y_of(max(start, end))
        bar_h = abs(y_of(end) - y_of(start))
        # A floor of two pixels, not nought point eight. A net-cash step is
        # small against enterprise value and drew as a hairline, leaving its
        # label floating in sienna above a bar nobody could see.
        body.append(
            f'<rect x="{centre - bar_w / 2:.1f}" y="{top_y:.1f}" '
            f'width="{bar_w:.1f}" height="{max(bar_h, 2.0):.1f}" '
            f'fill="{colour}" opacity="{1.0 if is_total else 0.86}"/>'
        )
        # A connector to the next bar, so the bars read as a waterfall
        # rather than as five unrelated columns.
        if index < len(geometry) - 1:
            y = y_of(end)
            body.append(
                f'<line x1="{centre + bar_w / 2:.1f}" y1="{y:.1f}" '
                f'x2="{centre + slot - bar_w / 2:.1f}" y2="{y:.1f}" '
                f'stroke="{theme.RULE}" stroke-width="1" '
                f'stroke-dasharray="2 2"/>'
            )
        body.append(
            _text(
                centre,
                top_y - 6,
                _money_precise(value),
                9.2,
                theme.INK,
                "middle",
                weight="500" if is_total else "400",
            )
        )
        # Two short lines: the labels are full phrases and will not fit on one.
        words = label.split()
        if len(words) > 1:
            body.append(
                _text(centre, height - 17, words[0], _FINE, theme.INK_MUTED,
                      "middle", font=_SANS)
            )
            body.append(
                _text(centre, height - 7, " ".join(words[1:]), 8.4,
                      theme.INK_MUTED, "middle", font=_SANS)
            )
        else:
            body.append(
                _text(centre, height - 12, label, _FINE, theme.INK_MUTED,
                      "middle", font=_SANS)
            )

    return _frame(
        width, height, "".join(body),
        label="Discounted cash flow bridge",
        describe=_describe(
            "From forecast cash flows and terminal value to equity value",
            [
                ("Present value of forecast", _money_precise(dcf.pv_forecast)),
                ("Present value of terminal", _money_precise(dcf.pv_terminal)),
                ("Enterprise value", _money_precise(dcf.enterprise_value)),
                # Follows the bar's own wording: a negative net-debt
                # position is cash being added, and calling it "less net
                # debt" reads as debt being added to enterprise value.
                (
                    "Less net debt"
                    if inputs.net_debt >= 0
                    else "Plus net cash",
                    _money_precise(abs(inputs.net_debt)),
                ),
                ("Equity value", _money_precise(dcf.equity_value)),
            ],
        ),
    )


def free_cash_flow_history(
    series: MetricSeries, width: float = 548, height: float = 232
) -> str | None:
    """Operating cash flow less capital expenditure, by filed year.

    Carried as its own chart because it is the series the valuation runs on,
    and a reader comparing a modelled target against a traded price needs to
    see whether the cash flow behind it has actually grown.
    """
    cash = _points(series, "operating_cash_flow")
    if len(cash) < 2:
        return None
    capex = {
        p.frame_label: abs(p.value)
        for p in _points(series, "capital_expenditures")
    }

    labels = [p.frame_label for p in cash]
    values = [p.value - capex.get(p.frame_label, 0.0) for p in cash]

    pad_l, pad_r, pad_t, pad_b = 52.0, 10.0, 42.0, 26.0
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    step = _nice_step(max(values) - min(0.0, min(values)))
    axis_top = _axis_top(max(values), step)
    axis_bottom = min(0.0, (int(min(values) / step)) * step)
    span = axis_top - axis_bottom or 1.0

    def y_of(value: float) -> float:
        return pad_t + plot_h - (value - axis_bottom) / span * plot_h

    subtitle = "Operating cash flow less capital expenditure, as filed"
    body = [_title_block(0, "Free cash flow", subtitle)]

    tick = axis_bottom
    while tick <= axis_top + step / 2:
        y = y_of(tick)
        body.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" '
            f'y2="{y:.1f}" stroke="{theme.RULE}" stroke-width="1"/>'
        )
        body.append(
            _text(pad_l - 8, y + 3.2, _money(tick), _TICK, theme.INK_MUTED, "end")
        )
        tick += step

    slot = plot_w / len(values)
    bar_w = min(slot * 0.56, 44.0)

    # The same window the model takes its base from, labelled with the
    # window. The rule used to be the mean of every filed year while the
    # model normalises over three, which coincide on Apple and diverge on
    # anyone with a longer or lumpier record.
    window = min(_BASE_WINDOW, len(values))
    mean = sum(values[-window:]) / window
    mean_y = y_of(mean)
    body.append(
        f'<line x1="{pad_l}" y1="{mean_y:.1f}" x2="{width - pad_r}" '
        f'y2="{mean_y:.1f}" stroke="{theme.ACCENT_2}" stroke-width="1.4" '
        f'stroke-dasharray="4 3"/>'
    )

    for index, (label, value) in enumerate(zip(labels, values)):
        centre = pad_l + slot * (index + 0.5)
        y = y_of(value)
        body.append(
            f'<rect x="{centre - bar_w / 2:.1f}" y="{y:.1f}" '
            f'width="{bar_w:.1f}" height="{max(y_of(0.0) - y, 0.6):.1f}" '
            f'fill="{theme.ACCENT}"/>'
        )
        body.append(
            _text(centre, y - 6, _money_precise(value), _LABEL, theme.INK,
                  "middle", weight="500")
        )
        body.append(
            _text(centre, height - 8, label, _TICK, theme.INK_MUTED, "middle")
        )

    # The mean label sits in the header rather than on its own rule. On the
    # rule it collided with the last bar's value label whenever the final
    # year landed near the average, which on Apple's filed record it does.
    key_x = width - pad_r
    body.append(
        _text(
            key_x,
            pad_t - 7,
            f"{window}-year mean {_money_precise(mean)}",
            8.6,
            theme.ACCENT_2,
            "end",
            font=_SANS,
        )
    )
    label_width = _FINE * 0.56 * len(
        f"{window}-year mean {_money_precise(mean)}"
    )
    body.append(
        f'<line x1="{key_x - label_width - 16:.1f}" y1="{pad_t - 10:.1f}" '
        f'x2="{key_x - label_width - 4:.1f}" y2="{pad_t - 10:.1f}" '
        f'stroke="{theme.ACCENT_2}" stroke-width="1.4" stroke-dasharray="4 3"/>'
    )
    return _frame(
        width, height, "".join(body),
        label="Free cash flow by filed year",
        describe=_describe(
            "Operating cash flow less capital expenditure, by filed year",
            [(p.frame_label, _money_precise(p.value)) for p in cash],
        ),
    )
