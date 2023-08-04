"""Contains functions for creating charts/plots."""

import altair as alt
import pandas as pd


ALTAIR_TIMEUNIT_TO_TIME_FORMAT = {
    "yearmonthdate": "%d %b, %Y",
    "yearweek": "%W, %Y",
    "yearmonth": "%b, %Y",
    "year": "%Y",
}

ALTAIR_TIMEUNIT_TO_PRETTY = {
    "yearmonthdate": "Day",
    "yearweek": "Week",
    "yearmonth": "Month",
    "year": "Year",
}


def get_chart_data(
    df: pd.DataFrame,
    transaction_field: str,
    group_by: str,
    timeunit: str,
    cumulative: bool,
    chart_type: str,
) -> alt.Chart:
    """Returns a chart object with the data transformed and ready to be plotted."""
    if cumulative:
        chart = (
            alt.Chart(df)
            .transform_impute(
                impute=f"cumulative_{transaction_field}",
                groupby=[group_by],
                key="date",
                value=0,
                method="value",
            )
            .transform_timeunit(
                ym=f"{timeunit}(date)",
            )
            .transform_aggregate(
                total_field=f"sum({transaction_field})",
                groupby=[
                    "ym",
                    group_by,
                ],
            )
            .transform_window(
                sort=[{"field": "ym", "order": "ascending"}],
                cumulative_total_field="sum(total_field)",
                frame=[None, 0],
                groupby=[group_by],
            )
        )
    else:
        chart = (
            alt.Chart(df)
            .transform_impute(
                impute=f"{transaction_field}",
                groupby=["date"],
                key="transaction_id",
                value=0,
                method="value",
            )
            .transform_timeunit(
                ym=f"{timeunit}(date)",
            )
        )

    if chart_type == "line":
        chart = chart.mark_line(interpolate="monotone", strokeWidth=2.5)
    elif chart_type == "bar":
        chart = chart.mark_bar()

    tooltip = [
        alt.Tooltip(
            "ym:T",
            title="Date",
            format=ALTAIR_TIMEUNIT_TO_TIME_FORMAT[timeunit],
        ),
        alt.Tooltip(
            "cumulative_total_field:Q" if cumulative else f"{transaction_field}:Q",
            title="Amount",
            format=",.1f",
        ),
    ]
    if group_by != "none":
        tooltip.append(alt.Tooltip(f"{group_by}:N", title=group_by.capitalize()))

    chart = chart.encode(
        x=alt.X("ym:T", title="Date"),
        y=alt.Y(
            "cumulative_total_field:Q" if cumulative else f"{transaction_field}:Q",
            title=f"Cumulative {transaction_field.capitalize()}"
            if cumulative
            else f"{transaction_field.capitalize()}",
        ),
        tooltip=tooltip,
        color=(
            alt.Color(
                f"{group_by}:N",
                title=f"{group_by.capitalize()}",
                legend=alt.Legend(direction="horizontal", orient="bottom"),
            )
            if group_by != "none"
            else alt.value("steelblue")
        ),
    ).properties(
        title=f"{'Cumulative ' if cumulative else ''}{transaction_field.capitalize()} {chart_type} chart grouped by {ALTAIR_TIMEUNIT_TO_PRETTY[timeunit]} {f', grouped by {group_by.capitalize()}' if group_by != 'none' else ''}"
    )
    return chart
