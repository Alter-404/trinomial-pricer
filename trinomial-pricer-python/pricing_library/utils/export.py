import pandas as pd

"""Small helpers to export pandas DataFrames to common formats.

This module provides convenience wrappers used by the web UI and
export utilities. The functions are intentionally thin wrappers around
pandas to keep call sites succinct.

Authors
-------
Mariano Benjamin
Noah Chikhi
"""


def export_dataframe_to_csv(df: pd.DataFrame, filename: str) -> None:
    """Write a DataFrame to CSV."""
    df.to_csv(filename, index=False)


def export_dataframe_to_excel(df: pd.DataFrame, filename: str) -> None:
    """Write a DataFrame to an Excel workbook."""
    df.to_excel(filename, index=False)
