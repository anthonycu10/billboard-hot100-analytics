# queries.py

import pandas as pd

def run_query(conn, query, params=None):
    return pd.read_sql_query(
        query,
        conn,
        params=params
    )