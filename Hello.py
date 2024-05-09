# Import required libraries
import streamlit as st
from streamlit.logger import get_logger
import plotly.express as px
import pandas as pd
import os
import warnings

warnings.filterwarnings("ignore")

# Set page config
st.set_page_config(page_title="Superstore!!!", page_icon=":bar_chart:", layout="wide")

LOGGER = get_logger(__name__)

def run():
    # Custom CSS to set the background color to dark red
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

    st.title(":bar_chart: Sample SuperStore EDA")
    st.markdown(
        "<style>div.block-container{padding-top:1rem;}</style>", unsafe_allow_html=True
    )

    # File uploader for user-provided files
    fl = st.file_uploader(":file_folder: Upload a file", type=(["csv", "txt", "xlsx", "xls"]))
    if fl is not None:
        filename = fl.name
        st.write(filename)
        df = pd.read_csv(fl, encoding="ISO-8859-1")
    else:
        #os.chdir("/")
        df = pd.read_csv("GlobalSuperstoreliteOriginal.csv", encoding="ISO-8859-1")

    # Fill any missing values with an empty string
    df.fillna('', inplace=True)

    # Ensure data types are consistent by converting to strings if necessary
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Region'] = df['Region'].astype(str)
    df['State'] = df['State'].astype(str)
    df['City'] = df['City'].astype(str)

    # Split layout into columns
    col1, col2 = st.columns((2))
    startDate = pd.to_datetime(df['Order Date']).min()
    endDate = pd.to_datetime(df['Order Date']).max()

    with col1:
        date1 = pd.to_datetime(st.date_input("Start Date", startDate))

    with col2:
        date2 = pd.to_datetime(st.date_input("End Date", endDate))

    # Filter data by date
    df = df[(df['Order Date'] >= date1) & (df['Order Date'] <= date2)].copy()

    # Sidebar filters
    st.sidebar.header("Choose your filter: ")
    region = st.sidebar.multiselect("Pick your Region", df['Region'].unique())
    if not region:
        df2 = df.copy()
    else:
        df2 = df[df['Region'].isin(region)]

    state = st.sidebar.multiselect("Pick the State", df2['State'].unique())
    if not state:
        df3 = df2.copy()
    else:
        df3 = df2[df2['State'].isin(state)]

    city = st.sidebar.multiselect("Pick the City", df3['City'].unique())

    if not region and not state and not city:
        filtered_df = df
    elif not state and not city:
        filtered_df = df[df['Region'].isin(region)]
    elif not region and not city:
        filtered_df = df[df['State'].isin(state)]
    elif state and city:
        filtered_df = df3[df['State'].isin(state) & df3['City'].isin(city)]
    elif region and city:
        filtered_df = df3[df['Region'].isin(region) & df3['City'].isin(city)]
    elif region and state:
        filtered_df = df3[df['Region'].isin(region) & df3['State'].isin(state)]
    elif city:
        filtered_df = df3[df3['City'].isin(city)]
    else:
        filtered_df = df3[
            df3['Region'].isin(region) & df3['State'].isin(state) & df3['City'].isin(city)
        ]

    # Ensure numeric columns are properly formatted
    filtered_df['Sales'] = pd.to_numeric(filtered_df['Sales'], errors='coerce')
    filtered_df['Profit'] = pd.to_numeric(filtered_df['Profit'], errors='coerce')
    filtered_df['Quantity'] = pd.to_numeric(filtered_df['Quantity'], errors='coerce')

    # Replace NaN values with 0
    filtered_df.fillna({'Sales': 0, 'Profit': 0, 'Quantity': 0}, inplace=True)

    # Group by category and handle missing data
    category_df = filtered_df.groupby(by=['Category'], as_index=False)['Sales'].sum()
    category_df.fillna(0, inplace=True)

    with col1:
        st.subheader("Category wise Sales")
        fig = px.bar(
            category_df,
            x="Category",
            y="Sales",
            text=["${:,.2f}".format(x) for x in category_df['Sales']],
            template="seaborn",
        )
        fig.update_layout(
            title="Category wise Sales", xaxis_title="Category", yaxis_title="Sales Amount"
        )
        fig.update_traces(marker_color="green")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Country wise Sales")
        country_sales = filtered_df.groupby('Country')['Sales'].sum().reset_index()
        country_sales.fillna(0, inplace=True)
        fig = px.pie(country_sales, values='Sales', names='Country', hole=0.5)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    # Time Series Analysis
    filtered_df['month_year'] = filtered_df['Order Date'].dt.to_period('M')
    st.subheader("Time Series Analysis")

    linechart = pd.DataFrame(
        filtered_df.groupby(filtered_df['month_year'].dt.strftime("%Y : %b"))['Sales'].sum()
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
    fig2.update_traces(line=dict(color="red"))
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("View Data of TimeSeries:"):
        st.write(linechart.T.style.background_gradient(cmap="Blues"))
        csv = linechart.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Data", data=csv, file_name="TimeSeries.csv", mime="text/csv"
        )

    # Treemap Analysis
    st.subheader("Hierarchical view of Sales using TreeMap")
    fig3 = px.treemap(
        filtered_df,
        path=['Region', 'Category', 'Sub-Category'],
        values='Sales',
        hover_data=['Sales'],
        color='Sub-Category',
    )
    fig3.update_traces(marker=dict(colors=[
        "#FF5733", "#FFC300", "#DAF7A6", "#C70039", "#FF5733", "#FFC300", "#DAF7A6", "#C70039"
    ]))
    fig3.update_layout(width=800, height=650)
    st.plotly_chart(fig3, use_container_width=True)

    # Scatter Plot Analysis
    data1 = px.scatter(
        filtered_df,
        x="Sales",
        y="Profit",
        size="Quantity",
        title="Relationship between Sales and Profits using Scatter Plot.",
        labels={"Sales": "Sales Amount", "Profit": "Profit Amount"}
    )
    data1['layout'].update(
        titlefont=dict(size=20),
        xaxis=dict(title="Sales", titlefont=dict(size=19)),
        yaxis=dict(title="Profit", titlefont=dict(size=19)),
    )
    st.plotly_chart(data1, use_container_width=True)

    # Download original dataset
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Data", data=csv, file_name="Data.csv", mime='text/csv')


if __name__ == "__main__":
    run()
