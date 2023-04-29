import numpy as np
import datetime
import time
import pandas as pd
import json
import pytz
import methods

client_id = ""  # replace this with your key
client_secret = ""  # replace with your secret
live = False  # choice True or False. If True, the bot runs on the deribit api and if False, the bot runs on the

amount = 0.1  # sets the amount of crypto to sell. BTC minimum contract is 0.1 and ETH is 1
trailing_options_switch = True  # if true, the bot opens trailing positions based on the trailing_price,
# else it skips it.
trailing_price = 0.09  # sets the price for the trailing orders. Trailing order are limited order sent to the order
# book at strike prices above the current price.
max_margin = 50  # Maximum margin threshold. If margin is above the threshold, bot wont place a trade
delta = 1 / 100  # sets the delta in percentage for the strike price. If BTC = 10,000 then the min strike price will
# be 10,100 for a 1/100 (1%) delta
min_sale_price = 0.008  # sets the minimum BTC price to sell the call option.
currency = "BTC"  # it should be either BTC or ETH


def get_strike_price(df, sale_price):
    # Filter the dataframe to keep only Type Put item options and for the oldest dates using parameterized SQL queries
    oldest_date = df['expiration'].min()
    filtered_data = df.query("expiration == @oldest_date and option_type == 'C' and strike_price >= @sale_price")

    # Calculate the absolute difference between the strike price and the sale price using numpy
    filtered_data['StrikeDiff'] = np.abs(filtered_data['strike_price'] - sale_price)

    return filtered_data


def check_margin_limits(ws, currency):
    """
    Checks if any of the margin limits are above 50% for a given currency.

    Args:
        ws (Workspace): The Workspace object that provides access to the trading account.
        currency (str): The currency to check the margin limits for.

    Returns:
        bool: True if any of the margin limits are above 50%, False otherwise.
    """
    # Get the portfolio margins for the given currency
    portfolio_margins = ws.get_account_summary(currency)['result']

    # Unpack the margin values into separate variables for readability
    initial_margin, projected_initial_margin = portfolio_margins['initial_margin'], portfolio_margins[
        'projected_initial_margin']
    maintenance_margin, projected_maintenance_margin = portfolio_margins['maintenance_margin'], portfolio_margins[
        'projected_maintenance_margin']

    # Check if any of the margin values are above 50%
    return initial_margin >= 50 or maintenance_margin >= 50 or projected_initial_margin >= 50 or \
        projected_maintenance_margin >= 50


def get_available_options(ws, underlying):
    """Retrieve the available options for a given underlying and currency.

    Args:
        ws (DeribitWS): Deribit websocket client.
        underlying (str): Underlying asset of the options.
        currency (str): Currency in which the options are traded. Defaults to 'BTC'.
        expired (bool): Whether to include expired options. Defaults to False.

    Returns:
        pd.DataFrame: DataFrame containing the available options with columns for instrument_name, underlying,
        option_type, strike, and expiration date.
    """
    # Retrieve the available instruments
    available_instruments = ws.available_instruments(underlying, 'option')

    # Convert to a pandas DataFrame
    available_options = pd.DataFrame(available_instruments, columns=['instrument_name'])

    # Split the instrument name into underlying, expiration date, option type, and strike price
    option_parts = available_options['instrument_name'].str.split('-', expand=True)
    available_options['underlying'] = option_parts[0]
    available_options['expiration'] = pd.to_datetime(option_parts[1], format='%d%b%y')
    available_options['option_type'] = option_parts[3]
    available_options['strike_price'] = option_parts[2].astype(float)

    return available_options


def covered_call(ws):
    # Retrieve available options for the underlying BTC
    global trailing_price
    available_options = get_available_options(ws, underlying=currency)

    # Check if account margin is above maximum threshold
    current_margin = check_margin_limits(ws, currency=currency)

    if current_margin == True:
        return_msg = f"Current account margin is above threshold ({max_margin}%). Trade not executed."
        return return_msg

    # Retrieve current BTC price and calculate sell price with delta
    btc_current_price = ws.get_index(currency)['result'][currency]
    btc_sell_price = btc_current_price * (1 + delta)

    # Retrieve list of instruments that are out of the money order from the smallest to the highest price
    out_of_money_options = get_strike_price(available_options, btc_sell_price)

    # Calculates the time until when the order is valid
    # Get the current time in Unix format
    current_time_unix = ws.get_time()['result']

    if len(out_of_money_options) == 0:
        return "No out-of-the-money options found. Trade not executed."

    # Sell option with market order for first out-of-the-money option
    option_name = out_of_money_options.iloc[0]['instrument_name']

    # Check if best bid price is above minimum bid set by the user
    best_bid_price = ws.ticker(option_name)['result']['best_bid_price']
    if best_bid_price > min_sale_price:
        sell_order = ws.sell(option_name, amount, type='market', label='Covered Call')
        trailing_price = best_bid_price
    else:
        sell_order = ws.sell(option_name, amount, type='limit', label='Covered Call', price=trailing_price)

    # Sell options with limit order for options in positions 2 and 4 (if available)
    if trailing_options_switch:
        for i, position in enumerate([2, 4]):
            if len(out_of_money_options) > position:
                option_name = out_of_money_options.iloc[position]['instrument_name']
                ws.sell(option_name, amount, type='limit', label='Covered Call', price=trailing_price)


        # Return JSON representation of sell order
        return_msg = json.dumps(sell_order, indent=4)

        return return_msg


while True:
    # convert current time to UTC
    utc = pytz.utc
    now_utc = datetime.datetime.now(tz=utc)

    # Create a datetime object for today at 8:05 UTC
    next_run = datetime.datetime(now_utc.year, now_utc.month, now_utc.day, 8, 5, 0, 0, tzinfo=pytz.utc)

    # If the current time is already past 8:05 UTC, set the datetime object for tomorrow at 8:05 UTC
    if now_utc.time() >= datetime.time(hour=8, minute=5, second=0):
        next_run += datetime.timedelta(days=1)

    time_until_next = (next_run - now_utc).total_seconds()
    print("The next run will take place in " + str(time_until_next) + " seconds.")
    # wait for 1 second before checking again
    time.sleep(time_until_next)
    ws = methods.DeribitWS(client_id=client_id, client_secret=client_secret, live=live)
    msg = covered_call(ws)
    print(msg)


#
# If you want to run the code using the a task on pythonanywhere.com, delete the While True loop above and uncomment
# the 3 rows below.
#

# ws = methods.DeribitWS(client_id=client_id, client_secret=client_secret, live=live)
# return_msg = covered_call(ws)
# print(return_msg)
