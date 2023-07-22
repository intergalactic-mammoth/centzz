import streamlit as st
import pandas as pd

def create_line_chart(df, x_col, y_col, title):
    chart_data = df[[x_col, y_col]]
    chart_data.set_index(x_col, inplace=True)
    st.caption(title)
    st.line_chart(chart_data, use_container_width=True)

def create_bar_chart(df, title, exclude_transfer=True):
    st.caption(title)
    st.bar_chart(df, use_container_width=True)
