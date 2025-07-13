# core/analytics.py

import json
import pandas as pd


def load_logs(path: str = 'sent_replies.json') -> pd.DataFrame:
    """
    Load the sent_replies.json log into a pandas DataFrame,
    parse timestamps, and extract date.
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    return df


def compute_stats(df: pd.DataFrame) -> dict:
    """
    Compute summary statistics from the replies DataFrame.
    Returns a dict with total, by_tag, by_day.
    """
    df_tags = df.explode('tags') if 'tags' in df.columns else df.copy()
    total = len(df)
    by_tag = df_tags['tags'].value_counts()
    by_day = df.groupby('date').size()
    return {
        'total': total,
        'by_tag': by_tag,
        'by_day': by_day
    }
