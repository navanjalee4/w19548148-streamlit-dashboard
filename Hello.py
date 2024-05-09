# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
from streamlit.logger import get_logger
import plotly.express as px
import pandas as pd
import os
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Superstore!!!", page_icon=":bar_chart:", layout="wide")

LOGGER = get_logger(__name__)


def run():
    # Custom CSS to set background color to dark red
    st.markdown(
        """
        <style>
        body {
            background-color: #8B0000 !important; /* Dark Red */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title(" :bar_chart: Sample SuperStore EDA")
    st.markdown(
        "<style>div.block-container{padding-top:1rem;}</style>", unsafe_allow_html=True
    )

    fl = st.file_uploader(
        ":file_folder: Upload a file", type=(["csv", "txt", "xlsx", "xls"])
    )
    if fl is not None:
        filename = fl.name
        st.write(filename)
        df = pd.read_csv(filename, encoding="ISO-8859-1")
    else:
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        DATA_FILE = os.path.join(SCRIPT_DIR, "GlobalSuperstoreliteOriginal.csv")
        df = pd.read_csv(DATA_FILE, encoding="ISO-8859-1")

    col1, col2 = st.columns((2))
    df["Order Date"] = pd.to_datetime(df["Order Date"])

    # Getting the min and max date
    startDate = pd.to_datetime(df["Order Date"]).min()
    endDate = pd.to_datetime(df["Order Date"]).max()

    with col1:
        date1 = pd.to_datetime(st.date_input("Start Date", startDate))

    with col2:
        date2 = pd.to_datetime(st.date_input("End Date", endDate))

    df = df[(df["Order Date"] >= date1) & (df["Order Date"] <= date2)].copy()

    st.sidebar.header("Choose your filter: ")
    # Create for Region
    region = st.sidebar.multiselect("Pick your Region", df["Region"].unique())
    if not region:
        df2 = df.copy()
    else:
        df2 = df[df["Region"].isin(region)]

    # Create for State
    state = st.sidebar.multiselect("Pick the State", df2["State"].unique())
    if not state:
        df3 = df2.copy()
    else:
        df3 = df2[df2["State"].isin(state)]

    # Create for City
    city = st.sidebar.multiselect("Pick the City", df3["City"].unique())

    # Filter the data based on Region, State and City

    if not region and not state and not city:
        filtered_df = df
    elif not state and not city:
        filtered_df = df[df["Region"].isin(region)]
    elif not region and not city:
        filtered_df = df[df["State"].isin(state)]
    elif state and city:
        filtered_df = df3[df["State"].isin(state) & df3["City"].isin(city)]
    elif region and city:
        filtered_df = df3[df["Region"].isin(region) & df3["City"].isin(city)]
    elif region and state:
        filtered_df = df3[df["Region"].isin(region) & df3["State"].isin(state)]
    elif city:
        filtered_df = df3[df3["City"].isin(city)]
    else:
        filtered_df = df3[
            df3["Region"].isin(region) & df3["State"].isin(state) & df3["City"].isin(city)
        ]

    category_df = filtered_df.groupby(by=["Category"], as_index=False)["Sales"].sum()

    with col1:
        st.subheader("Category wise Sales")
        fig = px.bar(
            category_df,
            x="Category",
            y="Sales",
            text=["${:,.2f}".format(x) for x in category_df["Sales"]],
            template="seaborn",
        )

        # Add title and axis labels
        fig.update_layout(
            title="Category wise Sales", xaxis_title="Category", yaxis_title="Sales Amount"
        )

        # Customize bar appearance
        fig.update_traces(
            marker_color="green",  # Change bar color
        )

        # Render bar chart
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Country wise Sales")
        country_sales = filtered_df.groupby("Country")["Sales"].sum().reset_index()
        fig = px.pie(country_sales, values="Sales", names="Country", hole=0.5)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    cl1, cl2 = st.columns((2))
    with cl1:
        with st.expander("Category_ViewData"):
            st.write(category_df.style.background_gradient(cmap="Blues"))
            csv = category_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Data",
                data=csv,
                file_name="Category.csv",
                mime="text/csv",
                help="Click here to download the data as a CSV file",
            )

    with cl2:
        with st.expander("Country_ViewData"):
            st.write(country_sales.style.background_gradient(cmap="Oranges"))
            csv = country_sales.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Data",
                data=csv,
                file_name="Country.csv",
                mime="text/csv",
                help="Click here to download the data as a CSV file",
            )

    filtered_df["month_year"] = filtered_df["Order Date"].dt.to_period("M")
    st.subheader("Time Series Analysis")

    linechart = pd.DataFrame(
        filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y : %b"))["Sales"].sum()
    ).reset_index()
    fig2 = px.line(
        linechart,
        x="month_year",
        y="Sales",
        labels={"Sales": "Amount"},
        height=500,
        width=1000,
        template="gridon",
    )

    # Change line color to red
    fig2.update_traces(line=dict(color="red"))

    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("View Data of TimeSeries:"):
        st.write(linechart.T.style.background_gradient(cmap="Blues"))
        csv = linechart.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Data", data=csv, file_name="TimeSeries.csv", mime="text/csv"
        )

    # Create a treem based on Region, category, sub-Category
    st.subheader("Hierarchical view of Sales using TreeMap")
    fig3 = px.treemap(
        filtered_df,
        path=["Region", "Category", "Sub-Category"],
        values="Sales",
        hover_data=["Sales"],
        color="Sub-Category",
    )

    # Change theme color
    fig3.update_traces(
        marker=dict(
            colors=[
                "#FF5733",
                "#FFC300",
                "#DAF7A6",
                "#C70039",
                "#FF5733",
                "#FFC300",
                "#DAF7A6",
                "#C70039",
            ]
        )
    )

    fig3.update_layout(width=800, height=650)
    st.plotly_chart(fig3, use_container_width=True)

    chart1, chart2, chart3, chart4 = st.columns((4))
    with chart1:
        st.subheader("Segment wise Sales")
        fig = px.pie(filtered_df, values="Sales", names="Segment", template="plotly_dark")
        fig.update_traces(text=filtered_df["Segment"], textposition="inside")
        st.plotly_chart(fig, use_container_width=True)

    with chart2:
        st.subheader("Category wise Sales")
        fig = px.pie(filtered_df, values="Sales", names="Category", template="gridon")
        fig.update_traces(text=filtered_df["Category"], textposition="inside")
        st.plotly_chart(fig, use_container_width=True)

    with chart3:
        # Compute product ID wise sales
        product_sales = filtered_df.groupby("Product ID")["Sales"].sum().reset_index()

        # Create a pie chart for product ID wise sales
        st.subheader("Product ID wise Sales")
        fig_product_sales = px.pie(
            product_sales, values="Sales", names="Product ID", hole=0.5
        )
        st.plotly_chart(fig_product_sales, use_container_width=True)

    with chart4:
        # Add a sidebar option to select Customer Id
        customer_id = st.sidebar.multiselect(
            "Pick the Customer Id", filtered_df["Customer ID"].unique()
        )

        # Filter the data based on Customer Id
        if not customer_id:
            filtered_df_customer = filtered_df.copy()
        else:
            filtered_df_customer = filtered_df[filtered_df["Customer ID"].isin(customer_id)]

        # Create a pie chart for sales based on Customer Id
        st.subheader("Customer ID wise Sales")
        customer_sales = (
            filtered_df_customer.groupby("Customer ID")["Sales"].sum().reset_index()
        )
        fig_customer_sales = px.pie(
            customer_sales, values="Sales", names="Customer ID", hole=0.5
        )
        st.plotly_chart(fig_customer_sales, use_container_width=True)

    import plotly.figure_factory as ff

    st.subheader(":point_right: Month wise Sub-Category Sales Summary")
    with st.expander("Summary_Table"):
        df_sample = df[0:5][
            ["Region", "State", "City", "Category", "Sales", "Profit", "Quantity"]
        ]
        fig = ff.create_table(df_sample, colorscale="Cividis")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("Month wise sub-Category Table")
        filtered_df["month"] = filtered_df["Order Date"].dt.month_name()
        sub_category_Year = pd.pivot_table(
            data=filtered_df, values="Sales", index=["Sub-Category"], columns="month"
        )
        st.write(sub_category_Year.style.background_gradient(cmap="Blues"))

    # Create a scatter plot
    data1 = px.scatter(filtered_df, x="Sales", y="Profit", size="Quantity")
    data1["layout"].update(
        title="Relationship between Sales and Profits using Scatter Plot.",
        titlefont=dict(size=20),
        xaxis=dict(title="Sales", titlefont=dict(size=19)),
        yaxis=dict(title="Profit", titlefont=dict(size=19)),
    )
    st.plotly_chart(data1, use_container_width=True)

    with st.expander("View Data"):
        st.write(filtered_df.iloc[:500, 1:20:2].style.background_gradient(cmap="Oranges"))

    # Download orginal DataSet
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Data", data=csv, file_name="Data.csv", mime="text/csv")


if __name__ == "__main__":
    run()
