from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image, ImageColor, ImageDraw, ImageFont

from shared.colored_logging import warning
from shared.constants import LOB_MAPPING


class PremiumsVisualizer:
    _color_map = {
        2016: "#FECB52",
        2017: "#EF553B",
        2018: "#00CC96",
        2019: "#AB63FA",
        2020: "#FFA15A",
        2021: "#19D3F3",
        2022: "#FF6692",
        2023: "#B6E880",
        2024: "#FF97FF",
        2025: "#636EFA",
        2026: "#8C564B",
        2027: "#17BECF",
    }
    _fallback_color = "#636EFA"
    _month_labels = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }

    def __init__(self, data):
        self.data = data

    def _prepare_chart_data(
        self,
        macro_lob: str,
        display_mode: str = "standard",
        color_map_style: str = "standard",
        current_uwy: int = 2026,
    ) -> tuple[pd.DataFrame, str, dict[int, str]]:
        if macro_lob:
            filtered_data = self.data[
                self.data["Reserving Class Code"].isin(LOB_MAPPING[macro_lob])
            ]
        else:
            filtered_data = self.data

        chart_data = (
            filtered_data.groupby(
                ["Policy Underwriting Year", "Policy Underwriting Month"]
            )["Expected GGWP (USD)"]
            .sum()
            .reset_index()
            .sort_values(["Policy Underwriting Year", "Policy Underwriting Month"])
        )

        chart_data["Cumulative Premiums"] = chart_data.groupby(
            "Policy Underwriting Year"
        )["Expected GGWP (USD)"].cumsum()

        metric = (
            "Cumulative Premiums"
            if display_mode == "cumulative"
            else "Expected GGWP (USD)"
        )
        years = sorted(chart_data["Policy Underwriting Year"].unique())

        if color_map_style == "focus":
            color_map = {
                year: "#D3D3D3" if year != current_uwy else "#EF553B" for year in years
            }
            chart_data["is_focus"] = (
                chart_data["Policy Underwriting Year"] == current_uwy
            )
            chart_data = chart_data.sort_values(
                ["is_focus", "Policy Underwriting Month"]
            )
        else:
            color_map = {
                year: self._color_map.get(year, self._fallback_color) for year in years
            }

        return chart_data, metric, color_map

    def _build_plotly_figure(
        self,
        chart_data: pd.DataFrame,
        metric: str,
        color_map: dict[int, str],
        color_map_style: str = "standard",
        current_uwy: int = 2026,
    ) -> go.Figure:
        fig = px.line(
            chart_data,
            x="Policy Underwriting Month",
            y=metric,
            color="Policy Underwriting Year",
            color_discrete_map=color_map,
            title="Expected GWP Over Time (By Year)",
            height=600,
        )

        if color_map_style == "focus":
            for trace in fig.data:
                if trace.name == str(current_uwy) or trace.name == current_uwy:
                    trace.line.width = 4
                else:
                    trace.line.width = 1.5
                    trace.opacity = 0.4

        return fig

    def get_figure(
        self,
        macro_lob: str,
        display_mode: str = "standard",
        color_map_style: str = "standard",
        current_uwy: int = 2026,
    ) -> go.Figure:
        chart_data, metric, color_map = self._prepare_chart_data(
            macro_lob=macro_lob,
            display_mode=display_mode,
            color_map_style=color_map_style,
            current_uwy=current_uwy,
        )
        return self._build_plotly_figure(
            chart_data=chart_data,
            metric=metric,
            color_map=color_map,
            color_map_style=color_map_style,
            current_uwy=current_uwy,
        )

    def write_image(
        self,
        macro_lob: str,
        output_path,
        display_mode: str = "standard",
        color_map_style: str = "standard",
        current_uwy: int = 2026,
        engine: str = "auto",
        width: int = 1600,
        height: int = 900,
        scale: int = 2,
    ) -> str:
        chart_data, metric, color_map = self._prepare_chart_data(
            macro_lob=macro_lob,
            display_mode=display_mode,
            color_map_style=color_map_style,
            current_uwy=current_uwy,
        )
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if engine in {"auto", "plotly"}:
            try:
                fig = self._build_plotly_figure(
                    chart_data=chart_data,
                    metric=metric,
                    color_map=color_map,
                    color_map_style=color_map_style,
                    current_uwy=current_uwy,
                )
                fig.write_image(
                    str(output_path),
                    width=width,
                    height=height,
                    scale=scale,
                )
                return "plotly"
            except Exception as exc:
                if engine == "plotly":
                    raise
                warning(
                    "Plotly static image export failed for "
                    f"{macro_lob}; using Pillow fallback instead. Details: {exc}"
                )

        self._write_image_with_pillow(
            chart_data=chart_data,
            metric=metric,
            color_map=color_map,
            output_path=output_path,
            color_map_style=color_map_style,
            current_uwy=current_uwy,
            width=width,
            height=height,
            title="Expected GWP Over Time (By Year)",
        )
        return "pillow"

    def _write_image_with_pillow(
        self,
        chart_data: pd.DataFrame,
        metric: str,
        color_map: dict[int, str],
        output_path: Path,
        color_map_style: str,
        current_uwy: int,
        width: int,
        height: int,
        title: str,
    ) -> None:
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        title_font = self._load_font(36, bold=True)
        text_font = self._load_font(20)
        small_font = self._load_font(18)

        margins = {
            "left": 110,
            "right": 240,
            "top": 110,
            "bottom": 90,
        }
        plot_left = margins["left"]
        plot_right = width - margins["right"]
        plot_top = margins["top"]
        plot_bottom = height - margins["bottom"]
        plot_width = plot_right - plot_left
        plot_height = plot_bottom - plot_top

        draw.text((plot_left, 30), title, fill="#1F2937", font=title_font)
        draw.rectangle(
            [(plot_left, plot_top), (plot_right, plot_bottom)],
            outline="#D1D5DB",
            width=2,
        )

        if chart_data.empty:
            draw.text(
                (plot_left + 30, plot_top + 30),
                "No data available for this line of business.",
                fill="#6B7280",
                font=text_font,
            )
            image.save(output_path, format="PNG")
            return

        y_min = min(0.0, float(chart_data[metric].min()))
        y_max = float(chart_data[metric].max())
        if y_min == y_max:
            y_max = y_min + 1.0

        y_padding = max((y_max - y_min) * 0.08, 1.0)
        y_min -= y_padding if y_min < 0 else 0.0
        y_max += y_padding
        month_values = list(range(1, 13))
        y_ticks = self._build_numeric_ticks(y_min, y_max, tick_count=6)

        def x_to_pixel(month: int) -> int:
            if len(month_values) == 1:
                return plot_left + (plot_width // 2)
            return int(
                plot_left
                + ((month - month_values[0]) / (month_values[-1] - month_values[0]))
                * plot_width
            )

        def y_to_pixel(value: float) -> int:
            return int(plot_bottom - ((value - y_min) / (y_max - y_min)) * plot_height)

        for y_tick in y_ticks:
            y_pixel = y_to_pixel(y_tick)
            draw.line(
                [(plot_left, y_pixel), (plot_right, y_pixel)],
                fill="#E5E7EB",
                width=1,
            )
            draw.text(
                (20, y_pixel - 10),
                self._format_axis_value(y_tick),
                fill="#4B5563",
                font=small_font,
            )

        for month in month_values:
            x_pixel = x_to_pixel(month)
            draw.line(
                [(x_pixel, plot_top), (x_pixel, plot_bottom)],
                fill="#F3F4F6",
                width=1,
            )
            draw.text(
                (x_pixel - 14, plot_bottom + 18),
                self._month_labels[month],
                fill="#4B5563",
                font=small_font,
            )

        year_series = {
            int(year): year_data.sort_values("Policy Underwriting Month")
            for year, year_data in chart_data.groupby("Policy Underwriting Year")
        }

        for year in sorted(year_series):
            year_data = year_series[year]
            points = [
                (
                    x_to_pixel(int(row["Policy Underwriting Month"])),
                    y_to_pixel(float(row[metric])),
                )
                for _, row in year_data.iterrows()
            ]
            if not points:
                continue

            line_color = self._resolve_line_color(
                color_map=color_map,
                year=year,
                color_map_style=color_map_style,
                current_uwy=current_uwy,
            )
            line_width = 6 if color_map_style == "focus" and year == current_uwy else 4
            draw.line(points, fill=line_color, width=line_width)
            for point in points:
                draw.ellipse(
                    [
                        (point[0] - 4, point[1] - 4),
                        (point[0] + 4, point[1] + 4),
                    ],
                    fill=line_color,
                    outline=line_color,
                )

        legend_x = plot_right + 35
        legend_y = plot_top + 10
        draw.text((legend_x, legend_y), "UWY", fill="#1F2937", font=text_font)
        for index, year in enumerate(sorted(year_series)):
            color = self._resolve_line_color(
                color_map=color_map,
                year=year,
                color_map_style=color_map_style,
                current_uwy=current_uwy,
            )
            item_y = legend_y + 40 + (index * 34)
            draw.line(
                [(legend_x, item_y + 10), (legend_x + 28, item_y + 10)],
                fill=color,
                width=4,
            )
            draw.text(
                (legend_x + 40, item_y),
                str(year),
                fill="#1F2937",
                font=small_font,
            )

        draw.text(
            (plot_left, plot_bottom + 50),
            "Policy Underwriting Month",
            fill="#1F2937",
            font=text_font,
        )
        draw.text(
            (plot_left, plot_top - 45),
            metric,
            fill="#4B5563",
            font=text_font,
        )

        image.save(output_path, format="PNG")

    def _resolve_line_color(
        self,
        color_map: dict[int, str],
        year: int,
        color_map_style: str,
        current_uwy: int,
    ) -> tuple[int, int, int]:
        color_value = color_map.get(year, self._fallback_color)
        if color_map_style == "focus" and year != current_uwy:
            color_value = "#BFC4CA"
        return ImageColor.getrgb(color_value)

    @staticmethod
    def _load_font(size: int, bold: bool = False):
        font_candidates = [
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
            "arialbd.ttf" if bold else "arial.ttf",
        ]
        for candidate in font_candidates:
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue
        return ImageFont.load_default()

    @staticmethod
    def _build_numeric_ticks(
        start: float, end: float, tick_count: int = 6
    ) -> list[float]:
        step = (end - start) / max(tick_count - 1, 1)
        return [start + (step * idx) for idx in range(tick_count)]

    @staticmethod
    def _format_axis_value(value: float) -> str:
        absolute = abs(value)
        if absolute >= 1_000_000_000:
            return f"{value / 1_000_000_000:.1f}B"
        if absolute >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if absolute >= 1_000:
            return f"{value / 1_000:.1f}K"
        return f"{value:.0f}"
