# app.py

import streamlit as st

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
from pathlib import Path

from queries import run_query
print(Path.cwd())
DB_PATH = Path(__file__).resolve().parent.parent / 'data' / 'charts.db'

st.markdown("""
<style>
    .page-header {
        background-color: #00A86B;
        padding: 25px 30px;
        border-radius: 12px;
        margin-bottom: 25px;
    }

    .page-header h1 {
        color: white;
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
    }

    .page-header p {
        color: #E8FFF5;
        margin: 8px 0 0 0;
        font-size: 1rem;
    }

    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #00A86B;
        padding: 15px;
        border-radius: 10px;
    }

    div[data-testid="stMetricValue"] {
        color: #00A86B;
    }

    div[data-testid="stMetricLabel"] {
        color: #00A86B;
    }

    div[data-baseweb="select"] > div {
        background-color: #FFFFFF;
        border-color: #00A86B;
        border-radius: 8px;
    }

    div.stButton > button {
        border: 1px solid #00A86B;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    div.stButton > button:hover {
        background-color: #00A86B;
        color: white;
        border-color: #00A86B;
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0, 168, 107, 0.25);
    }

    .success-card {
        background-color: #FFF4CC;
        border: 1px solid #E6C85C;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 10px 0 20px 0;
    }

    .success-label {
        color: #8A6D1D;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 1px;
    }

    .success-title {
        color: #22272E;
        font-size: 1.3rem;
        font-weight: 700;
        margin-top: 4px;
    }

    .success-subtitle {
        color: #5F5A45;
        font-size: 0.8rem;
        margin-top: 4px;
    }
</style>""", unsafe_allow_html=True)

conn = sqlite3.connect(DB_PATH)

@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_connection()

st.markdown(
    """
    <div class="page-header">
        <h1>Billboard Hot 100 Explorer</h1>
        <p>Explore artists, songs, chart performance, and Billboard Hot 100 history (as of 07-18-2026)</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# Popular Artists Shortcut
popular_artists_query = """
SELECT
    a.artist_id,
    a.artist_name,
    COUNT(*) AS chart_appearances
FROM fact_hot100 f

JOIN dim_date d
    ON f.date_id = d.date_id

JOIN bridge_song_artist b
    ON f.song_id = b.song_id

JOIN dim_artist2 a
    ON b.artist_id = a.artist_id

WHERE d.chart_date >= (
    SELECT date(MAX(chart_date), '-6 years')
    FROM dim_date
)

GROUP BY
    a.artist_id,
    a.artist_name

ORDER BY
    chart_appearances DESC

LIMIT 24
"""

popular_artists = pd.read_sql_query(
    popular_artists_query,
    conn
)

st.markdown(
    '<h3 style="color: #00A86B; margin-bottom: 0.5rem;">Popular Artists</h3>',
    unsafe_allow_html=True
)

with st.container(height=250):
    cols = st.columns(4)

    for i, artist_row in popular_artists.iterrows():
        with cols[i % 4]:
            if st.button(
                artist_row["artist_name"],
                key=f"popular_artist_{artist_row['artist_id']}",
                use_container_width=True
            ):
                st.session_state["selected_artist_id"] = artist_row["artist_id"]

artist_query = """
SELECT
    artist_id,
    artist_name
FROM dim_artist2
ORDER BY artist_name
"""

artists = run_query(conn, artist_query)

artist_options = artists.to_dict("records")

artist_ids = [
    artist["artist_id"]
    for artist in artist_options
]

default_index = 0

if "selected_artist_id" in st.session_state:
    if st.session_state["selected_artist_id"] in artist_ids:
        default_index = artist_ids.index(
            st.session_state["selected_artist_id"]
        )

artist = st.selectbox(
    "Search for an artist",
    artist_options,
    index=default_index,
    format_func=lambda x: x["artist_name"]
)

selected_artist_id = artist["artist_id"]

st.session_state["selected_artist_id"] = selected_artist_id

artist_summary_query = """
SELECT *
from vw_artist_summary
WHERE artist_id = ?
"""

artist_summary = pd.read_sql_query(
    artist_summary_query,
    conn,
    params = [selected_artist_id]
)

row = artist_summary.iloc[0]

st.subheader(
    f"{artist["artist_name"]}'s Billboard Hot 100 Career Overview"
)
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Hot 100 Songs",
    row["number_of_bb100charted_songs"]
)

col2.metric(
    "#1 Songs",
    row["number_of_1_songs"]
)

col3.metric(
    "Weeks at #1",
    row["total_weeks_at_1"]
)

col4.metric(
    "Top 10 Songs",
    row["number_of_top10_songs"]
)
st.divider()
st.subheader(
    f"All of {artist["artist_name"]}'s Billboard Hot 100 Charted Songs"
)
st.caption("Songs are ordered by most recent chart appearance.")

# Add all the artist's songs
song_query = """
SELECT
    vs.song_id,
    vs.song_title,
    vs.original_artist_string,
    peak_position,
    debut_position,
    date(first_bb100_chart_date),
    weeks_in_bb100chart,
    weeks_in_top10,
    weeks_at_1,
    date(latest_bb100_chart_date)
FROM vw_song_summary vs
JOIN bridge_song_artist b on vs.song_id = b.song_id
JOIN dim_artist2 a on b.artist_id = a.artist_id
WHERE b.artist_id = ?
ORDER BY date(latest_bb100_chart_date) DESC, peak_position ASC
"""

artist_songs = pd.read_sql_query(
    song_query,
    conn,
    params=[selected_artist_id]
)

st.dataframe(
    artist_songs.drop(columns=["song_id", "weeks_in_top10", "weeks_at_1", "original_artist_string"]).rename(columns={
        "song_title": "Song",
        "peak_position": "Peak",
        "debut_position": "Debut",
        "date(first_bb100_chart_date)": "Debut Date",
        "weeks_in_bb100chart": "Weeks Charted",
        "date(latest_bb100_chart_date)": "Latest Charted Date"
    }),
    width='stretch',
    hide_index=True
)
st.caption("**Peak**: highest position reached, **Debut**: first-week position")

st.divider()

# Song Analysis
song = st.selectbox(
    "Explore a song",
    artist_songs["song_title"].tolist()
)

artist_song = artist_songs.loc[
    artist_songs["song_title"] == song
].iloc[0]
song_title = artist_song["song_title"]
original_artist = artist_song["original_artist_string"]

st.markdown(f"### <u>{song}</u>— {original_artist}", unsafe_allow_html=True)

s_col1, s_col2, s_col3, s_col4 = st.columns(4)

s_col1.metric(
        "Peak Position",
        f"#{artist_song['peak_position']}",
        delta=f"Debuted #{artist_song['debut_position']}"
    )

s_col2.metric(
        "Weeks on Hot 100",
        artist_song["weeks_in_bb100chart"]
    )

s_col3.metric(
        "Weeks at #1",
        artist_song["weeks_at_1"]
    )

s_col4.metric(
        "Weeks in Top 10",
        artist_song["weeks_in_top10"]
    )

st.markdown("### Song Chart History")

st.caption("Tracking the song's Billboard Hot 100 position over the song's chart run")

chart_query = """
SELECT 
    d.chart_date,
    f.rank
FROM fact_hot100 f

JOIN dim_date d 
    ON f.date_id = d.date_id

JOIN dim_song s 
    ON f.song_id = s.song_id

JOIN bridge_song_artist b 
    ON s.song_id = b.song_id

JOIN dim_artist2 a
    ON b.artist_id = a.artist_id

WHERE s.song_title = ?
AND a.artist_id = ?

ORDER BY d.chart_date
"""

chart_history = pd.read_sql_query(
    chart_query,
    conn,
    params = [song, selected_artist_id]
)

fig = px.line(
    chart_history,
    x="chart_date",
    y="rank",
    title=f"{song}: Billboard Hot 100 Performance",
    labels={
        "chart_date": "Chart Date",
        "rank": "Billboard Hot 100 Rank"
    }
)

fig.update_layout(
    template="plotly_dark",
    yaxis=dict(
        autorange="reversed"
    ),
    hovermode="x unified",
    margin=dict(l=20, r=20, t=60, b=20)
)

fig.update_traces(
    line=dict(
        color="#00A86B",
        width=3
    ),
    mode="lines+markers",
    marker=dict(
        size=6
    )
)

st.plotly_chart(
    fig,
    width='stretch'
)

st.divider()
# Weighted Best Billboard Song
best_song_query = """
SELECT 
vs.*,
s.original_artist_string
FROM vw_artist_songs_scored vs
JOIN dim_song s on vs.song_id = s.song_id
WHERE artist_id = ?
and song_score_ranked = 1
"""

best_song = pd.read_sql_query(
    best_song_query,
    conn,
    params=[selected_artist_id]
)

if not best_song.empty:

    best = best_song.iloc[0]

    st.markdown(
    f"""
    <div class="success-card">
        <div class="success-label">Artist's 'Most Billboard Hot 100 Successful' Song</div>
        <div class="success-title"><u>{best['song_title']}</u>— {best['original_artist_string']}</div>
        <div class="success-subtitle">
            Calculated using a weighted Billboard performance score based on peak position, total weeks in BB Hot 100, total weeks in Top 10, and total weeks at #1
        </div>
    </div>
    """,  unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Peak Position",
        f"#{best['peak_position']}"
    )

    col2.metric(
        "Weeks on Hot 100",
        best["weeks_in_bb100chart"]
    )

    col3.metric(
        "Weeks at #1",
        best["weeks_at_1"]
    )

    col4.metric(
        "Weeks in Top 10",
        best["weeks_in_top10"]
    )
