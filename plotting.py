import streamlit as st
import pandas as pd


def create_line_chart(df, x_col, y_col, title):
    """Creates a line chart from a dataframe with the given x and y columns."""
    chart_data = df[[x_col, y_col]]
    chart_data.set_index(x_col, inplace=True)
    st.caption(title)
    st.line_chart(chart_data, use_container_width=True)


def create_bar_chart(df, title):
    """Creates a bar chart from a dataframe.

    The assumed dataframe structure is unstacked such that the
    index is the x-axis and the columns are the y-axis.
    Different columns represent different categories of data."""
    st.caption(title)
    st.bar_chart(df, use_container_width=True)
