# SIMPLE WEB APP

# How to run this web app:
# open the shell in the Deliverable repo
# `conda activate dev`
# `streamlit run team_projects/example_member/web_app/simple_web_app.py`

# extra comment


import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

connection_string = st.secrets["POSTGRES_CONNECTION_STRING"]
# connection_string = os.environ["POSTGRES_CONNECTION_STRING"]

st.title("COVID Review Insights")
st.markdown("This app explores Deliverable review data and COVID infection data.")


@st.cache
def load_covid_data(connection_string):
    """Get data from database"""
    engine = create_engine(connection_string)

    return pd.read_sql_query(
        """
        select municipality_name, date_of_publication, sum(total_reported) as total_reported
        from covid.municipality_totals_daily mtd
        where municipality_name in ('Groningen', 'Amsterdam', 'Rotterdam')
        and date_of_publication > '2020-12-31'
        group by municipality_name, date_of_publication
        order by municipality_name, date_of_publication
        """,
        con=engine,
    )


@st.cache
def load_review_data(connection_string):
    engine = create_engine(connection_string)
    return pd.read_sql_query(
        """
    select review_date, location_city, count(*) as n_reviews,
    AVG(rating_delivery) as avg_del_score, AVG(rating_food) as avg_food_score from (
        select DATE(datetime) review_date, rating_delivery, rating_food, location_city from public.reviews rv
        left join (select restaurant_id, location_city from restaurants) locs
        on rv.restaurant_id = locs.restaurant_id
        where datetime > '2020-12-31'
        and location_city in ('Groningen', 'Amsterdam', 'Rotterdam')
    ) t
    group by review_date, location_city
    """,
        con=engine,
    )


with st.spinner("Loading COVID data ..."):
    df_covid = load_covid_data(connection_string)
    df_review = load_review_data(connection_string)

if st.checkbox("Show raw COVID data"):
    st.write(df_covid)


## TODO Add filters
dmin = df_covid["date_of_publication"].dt.date.min()
dmax = df_covid["date_of_publication"].dt.date.max()
dates = st.slider("Pick data", dmin, dmax, value=[dmin, dmax])


def filter_data(df, dmin, dmax):
    return df.loc[
        ((df["date_of_publication"].dt.date >= dmin) & (df["date_of_publication"].dt.date <= dmax))
    ]


## TODO Add plots
def plot_covid(df_covid):
    fig = px.line(
        df_covid,
        x="date_of_publication",
        y="total_reported",
        color="municipality_name",
        labels={"date_of_publication": "", "total_reported": "Cases reported"},
    )

    fig.update_layout({"legend_title_text": ""})
    return fig


# Filter and plot data
df_covid_filtered = filter_data(df_covid, dates[0], dates[1])
st.plotly_chart(plot_covid(df_covid_filtered))
