# Project Goal

Build an analytics warehouse for Billboard Hot 100 data that supports reusable reporting and dashboards.

## Fact Table

`fact_hot100`

Grain: One row = one song on one Billboard chart week.
Primary Key: {date_id, rank}

Columns:

- song_id (FK)
- date_id (FK)
- rank
- peak_position
- last_position
- weeks_on_chart
- is_new

## Dimensions

`dim_artist2`

- artist_id
- artist_name

This artist table is built after having cleaned/parsed through artist string names. 

`dim_song`

- song_id
- title
- artist_name

`dim_date`

- date_id
- chart_date
- year
- month
- quarter
- week

## Bridge

`bridge_song_artist`

- song_id
- artist_id
- artist_role
- artist_order

Building the bridge_song_artist incorporated Gemini API to parse through artist names, to separate collaborations/features.