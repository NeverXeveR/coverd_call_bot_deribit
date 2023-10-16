import numpy as np
import datetime
import time
import pandas as pd
import json
import pytz
import methods


def get_iv_rank(ws, currency, days, end_date_ms, RESOLUTION="1D"):

    # Calculate the start date as the end date minus the specified number of days in milliseconds
    start_date_ms = end_date_ms - (days * 24 * 60 * 60 * 1000)

    volatility = ws.get_volatility_index_data(
        currency, start_date_ms, end_date_ms, RESOLUTION)['result']['data']

    # convert the volatility data to a dataframe
    df_volatility = pd.DataFrame(volatility)

    # rename the columns of the dataframe to: date, open, high, low, and close
    df_volatility.columns = ['date', 'open', 'high', 'low', 'close']

    # converts the date column to datetime format
    df_volatility['date'] = pd.to_datetime(df_volatility['date'], unit='ms')

    # calculate the IV rank for the last column of the df_volatility dataframe,
    # using the formula (close – min(close)) / (max(close) – min(low)) * 100
    min_IV = df_volatility['close'].min()
    max_IV = df_volatility['close'].max()

    # numerator should get all values from df_volatility['close'] and subtract the min_IV
    # denominator should get the max_IV minus the min_IV
    numerator = df_volatility['close'] - min_IV
    denominator = max_IV - min_IV

    df_volatility['IV rank'] = (numerator / denominator) * 100

    return df_volatility['IV rank'].iloc[-1]
