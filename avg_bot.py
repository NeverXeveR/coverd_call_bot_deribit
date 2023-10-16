import time
import pandas as pd
import methods
import volatility as vol
from setup import *


import logging

# Configure the root logger with a file handler and console (screen) handler
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),  # Save log messages to a file
        logging.StreamHandler(),  # Print log messages to the console
    ],
)


def connect_deribit():
    ws = methods.DeribitWS(client_id=client_id, client_secret=client_secret, live=live)

    return ws


def calculate_iv_rank(
    IV_RANK,
    end_date_ms,
    currency,
    days,
    resolution,
    IV_RANK_FREQ_UPADATE,
    CURRENCY,
    SYMBOL,
):
    OLD_IV_RANK = IV_RANK

    # check if IV Rank needs to be updated. It should be updated every day
    current_time = int(time.time() * 1000)

    # if current time is more than 24 hours from the last update, then update IV Rank
    if (current_time - end_date_ms) > IV_RANK_FREQ_UPADATE * 60 * 60 * 1000:
        IV_RANK = vol.get_iv_rank(
            ws, currency, days, end_date_ms, RESOLUTION=resolution
        )
        end_date_ms = current_time

        current_time = pd.to_datetime(current_time, unit="ms")

        # once IV_RANK is updated, MM and PT orders should be adjusted to new IV
        correct_orders(IV_RANK, OLD_IV_RANK, LABEL_MM, CURRENCY, SYMBOL)

    return IV_RANK, end_date_ms


def correct_orders(IV_RANK, OLD_IV_RANK, LABEL_MM, CURRENCY, SYMBOL):
    # get all current positions by label
    open_orders_mm_buy = ws.get_open_orders_by_label(CURRENCY, LABEL_MM + "_buy")
    open_orders_mm_sell = ws.get_open_orders_by_label(CURRENCY, LABEL_MM + "_sell")
    open_orders_pt = ws.get_open_orders_by_label(CURRENCY, "Profit_taking")

    # Calculate new Interval:
    INTERVAL_OLD = get_interval(OLD_IV_RANK, interval_ranges)
    INTERVAL_NEW = get_interval(IV_RANK, interval_ranges)

    # loop through the dictionary open_orders_mm_buy["result"], get the price and divide it by (1 + INTERVAL_OLD) and Multiply it by (1 + INTERVAL_NEW)
    # for each mm_buy, I will place a new order with the new price
    for i in range(len(open_orders_mm_buy["result"])):
        PRICE = open_orders_mm_buy["result"][i]["price"]
        NEW_PRICE = round(PRICE / (1 - INTERVAL_OLD) * (1 - INTERVAL_NEW), 0)
        ws.edit_by_label(NEW_PRICE)

        print("Buy - Old price: ", PRICE, " and new price: ", NEW_PRICE)

    for i in range(len(open_orders_mm_sell["result"])):
        PRICE = open_orders_mm_sell["result"][i]["price"]
        NEW_PRICE = round(PRICE / (1 + INTERVAL_OLD) * (1 + INTERVAL_NEW), 0)
        ws.edit_by_label(NEW_PRICE)

        print("Sell - Old price: ", PRICE, " and new price: ", NEW_PRICE)

    for i in range(len(open_orders_pt["result"])):
        PRICE = open_orders_pt["result"][i]["price"]
        AMOUNT = open_orders_pt["result"][i]["amount"]

        if AMOUNT < 0:
            NEW_PRICE = round(PRICE / (1 + INTERVAL_OLD) * (1 + INTERVAL_NEW), 0)
        else:
            NEW_PRICE = round(PRICE / (1 - INTERVAL_OLD) * (1 - INTERVAL_NEW), 0)

        ws.edit_by_label(
            instrument_name=SYMBOL,
            label="Profit_taking",
            amount=AMOUNT,
            price=NEW_PRICE,
        )

        logging.info(
            f"PT Order - Old price: {PRICE} and new price: {NEW_PRICE} and amount: {AMOUNT}"
        )
        logging.info(f"Old IV Rank: {OLD_IV_RANK} and new IV Rank: {IV_RANK}")
        logging.info(f"Old Interval: {INTERVAL_OLD} and new Interval: {INTERVAL_NEW}")


def calculate_profit(IV_RANK, profit_ranges):
    for (lower, upper), profit in profit_ranges.items():
        if lower <= IV_RANK < upper:
            PROFIT = profit
            break

    return PROFIT


def get_interval(IV_RANK, interval_ranges):
    for (lower, upper), interval in interval_ranges.items():
        if lower <= IV_RANK < upper:
            INTERVAL = interval
            break

    return INTERVAL


def place_order(
    current_position, IV_RANK, INDEX_NAME=INDEX_NAME, ORDER_RESTRICITION=None
):
    # get the current price
    # ORDER_RESTRICTION can be None, "BUY_ONLY" or "SELL_ONLY"

    current_price = ws.get_index_price(INDEX_NAME)["result"]["index_price"]

    INTERVAL = get_interval(IV_RANK, interval_ranges)

    # calculate the distance between orders
    distance = current_price * INTERVAL

    # calculate the price for each order and round it to the nearest dollar
    # checks if SKEW is newutral, bullish or bearish
    if SKEW == "Neutral":
        BID_PRICE = round(current_price - distance, 0)
        ASK_PRICE = round(current_price + distance, 0)
    elif SKEW == "Bullish":
        BID_PRICE = round(current_price - distance * 1 / 10, 0)
        ASK_PRICE = round(current_price + distance * 9 / 10, 0)
    elif SKEW == "Bearish":
        BID_PRICE = round(current_price - distance * 9 / 10, 0)
        ASK_PRICE = round(current_price + distance * 1 / 10, 0)

    # calculate the order size for each order
    BID_SIZE = ORDER_START_SIZE
    ASK_SIZE = ORDER_START_SIZE

    # place the bid orders

    if ORDER_RESTRICITION == "BUY_ONLY" or ORDER_RESTRICITION == None:
        for i in range(ORDER_PAIRS):
            # buy(self, instrument, amount, type, label, price=0.00)
            # @TODO: check if the order is placed correctly.
            # If not, needs to ge the error and fix.
            # It is possible that price changes and order is ITM
            ws.buy(SYMBOL, BID_SIZE, "limit", LABEL_MM + "_buy", BID_PRICE)

            # increment the price and size for each order
            if INTERVAL_TYPE == "linear":
                BID_PRICE = round(BID_PRICE - distance, 0)
            elif INTERVAL_TYPE == "geometrical":
                BID_PRICE = round(BID_PRICE / (1 + INTERVAL) ** (i + 1), 0)

            BID_SIZE = BID_SIZE + ORDER_STEP_SIZE

    # place the ask orders
    if ORDER_RESTRICITION == "SELL_ONLY" or ORDER_RESTRICITION == None:
        for i in range(ORDER_PAIRS):
            ws.sell(SYMBOL, ASK_SIZE, "limit", LABEL_MM + "_sell", ASK_PRICE)

            # increment the price and size for each order
            if INTERVAL_TYPE == "linear":
                ASK_PRICE = round(ASK_PRICE + distance, 0)
            elif INTERVAL_TYPE == "geometrical":
                ASK_PRICE = round(ASK_PRICE * (1 + INTERVAL) ** (i + 1), 0)

            ASK_SIZE = ASK_SIZE + ORDER_STEP_SIZE

    return


def get_open_orders(CURRENCY, LABEL_BUY, LABEL_SELL, PROFIT_TAKING):
    # get open orders by currency
    open_orders = ws.get_open_orders_by_currency(CURRENCY)["result"]

    # if an open order has label "Profit_taking", then it is a PT order
    open_orders_pt = [i for i in open_orders if i["label"] == PROFIT_TAKING]

    # exclude all open orders with label "Profit_taking"
    open_orders = [i for i in open_orders if i["label"] != PROFIT_TAKING]

    # if a open order has direction "buy", then it is a MM buy order
    open_orders_mm_buy = [i for i in open_orders if i["direction"] == "buy"]

    # if a open order has direction "sell" and label different than "Profit_taking", then it is a MM sell order
    open_orders_mm_sell = [i for i in open_orders if i["direction"] == "sell"]

    return open_orders_mm_buy, open_orders_mm_sell, open_orders_pt


def open_PT_order(current_position, IV_RANK):
    CURRENT_SIZE = current_position["size"]

    # place PT order in the opposite direction
    if CURRENT_SIZE > 0:
        PROFIT = calculate_profit(IV_RANK, profit_ranges)
        PRICE = round(current_position["average_price"] * (1 + PROFIT), 0)
        ws.sell(SYMBOL, abs(CURRENT_SIZE), "limit", "Profit_taking", PRICE)
    elif CURRENT_SIZE < 0:
        PROFIT = calculate_profit(IV_RANK, profit_ranges)
        PRICE = round(current_position["average_price"] * (1 - PROFIT), 0)
        ws.buy(SYMBOL, abs(CURRENT_SIZE), "limit", "Profit_taking", PRICE)

    return


def position_scenario(
    current_position,
    open_orders_mm_buy,
    open_orders_mm_sell,
    open_orders_pt,
    ORDER_PAIRS=ORDER_PAIRS,
):
    """
    Combining them together it is possible to have the following scenarios:
        position
        order MM
        order PT

        There are 2 major scenarios:
            1. There is no open position
                a. There is no open order
                b. There are equal number of open buy and sell orders
                c. There are non-sense open orders
            2. There is an open position
                a. There is no Order_MM and no Order_PT
                b. There is Order_MM and no Order_PT
                c. There is Order_MM and Order_PT
                d. There is no Order_MM and Order_PT


        Scenario      |   Position   |   Order_MM    |   Order_PT    |   Action
        1a            |   None       |   None        |   None        |   Place buy and sell orders
        1b            |   None       |   X           |   X           |   Pass as long as #_order_buy = #_order_sell
        1c            |   None       |   Irrelevant  |   Irrelevant  |   Cancel all
        ---------------------------- ---------------------------------------------------------------------------------------------------------------------
        Scenario      |   Position   |   Order_MM    |   Order_PT    |   Action
                      |              | Buy   | Sell  | Buy  | Sell   |

        2a.1          |      x       | None  | None  | None | None   |   place PT order in oposite direction
        ---------------------------- -----------------------------------------------
        2b.1          |      x       |   X   | None  | None | None   |   Cancel order_MM and place PT order in oposite direction
        2b.2          |      x       | None  |  X    | None | None   |   Cancel order_MM and place PT order in oposite direction
        2b.3          |      x       |  X    |  X    | None | None   |   Cancel order_MM and place PT order in oposite direction
        ---------------------------- -----------------------------------------------
        2c.1          |      x       |  X    | None  |  X   | None   |   Cancel PT order and place PT order in oposite direction
        2c.2          |      x       |  X    | None  | None |  X     |   Check size of position and order, if different, cancel order_MM and place PT order in oposite direction
        2c.3          |      x       |  X    | None  |  X   |  X     |   Cancel PT order and check size of position and order, if different, cancel order_MM and place PT order in oposite direction

        2c.4          |      x       | None  |  X    |  X   | None   |   Check size of position and order, if different, cancel order_MM and place PT order in oposite direction
        2c.5          |      x       | None  |  X    | None |  X     |   Cancel PT order and place PT order in oposite direction
        2c.6          |      x       | None  |  X    |  X   |  X     |   Cancel PT order and check size of position and order, if different, cancel order_MM and place PT order in oposite direction
        ---------------------------- -----------------------------------------------
                      | Long | Short | Buy   | Sell  | Buy  | Sell   |
        2c.7          |  x   |       |  X    |  X    |  X   | None   |   Cancel Order_MM_Buy and Order_PT_Buy
        2c.8          |  x   |       |  X    |  X    | None |  X     |   Cancel Order_MM_Buy
        2c.9          |  x   |       |  X    |  X    |  X   |  X     |   Cancel Order_MM_Buy and Order_PT_Buy
        2c.10         |      |  x    |  X    |  X    |  X   | None   |   Cancel Order_MM_Sell and Order_PT_Sell
        2c.11         |      |  x    |  X    |  X    | None |  X     |   Cancel Order_MM_Sell
        2c.12         |      |  x    |  X    |  X    |  X   |  X     |   Cancel Order_MM_Sell and Order_PT_Sell
        ---------------------------- -----------------------------------------------
        2d.1          |      x       | None  | None  |  X   | None   |   Cancel order PT and place PT order in oposite direction
        2d.2          |      x       | None  | None  | None |  X     |   Cancel order PT and place PT order in oposite direction
        2d.3          |      x       | None  | None  |  X   |  X     |   Cancel order PT and place PT order in oposite direction

        ---------------------------- -----------------------------------------------
    """

    CURRENT_SIZE = current_position["size"]

    logging.info(f"Calculating scenario... ")

    # count number of open_orders_pt['result']['direction'] is buy
    if open_orders_pt != 0:
        NUMBER_OPEN_ORDER_PT_BUY = len(
            [i for i in open_orders_pt if i["direction"] == "buy"]
        )
        NUMBER_OPEN_ORDER_PT_SELL = len(
            [i for i in open_orders_pt if i["direction"] == "sell"]
        )
    else:
        NUMBER_OPEN_ORDER_PT_BUY = 0
        NUMBER_OPEN_ORDER_PT_SELL = 0

    NUMBER_OPEN_ORDER_MM_BUY = len(
        [i for i in open_orders_mm_buy if i["direction"] == "buy"]
    )

    NUMBER_OPEN_ORDER_MM_SELL = len(
        [i for i in open_orders_mm_sell if i["direction"] == "sell"]
    )

    NUMBER_OPEN_ORDER_MM = NUMBER_OPEN_ORDER_MM_BUY + NUMBER_OPEN_ORDER_MM_SELL

    NUMBER_OPEN_ORDER_PT = NUMBER_OPEN_ORDER_PT_BUY + NUMBER_OPEN_ORDER_PT_SELL

    logging.info(
        f"Number of open orders buy: {NUMBER_OPEN_ORDER_MM_BUY} and sell: {NUMBER_OPEN_ORDER_MM_SELL} and PT: {NUMBER_OPEN_ORDER_PT}"
    )

    # Loop Scenario 1
    if CURRENT_SIZE == 0:
        # 1a
        if (
            NUMBER_OPEN_ORDER_MM_BUY == 0
            and NUMBER_OPEN_ORDER_MM_SELL == 0
            and NUMBER_OPEN_ORDER_PT == 0
        ):
            logging.info(
                f"Scenario 1a - No Open orders or position - Placing new buy and sell orders"
            )
            place_order(current_position, IV_RANK)
        # 1b
        elif (
            NUMBER_OPEN_ORDER_MM_BUY == NUMBER_OPEN_ORDER_MM_SELL
            and NUMBER_OPEN_ORDER_MM == ORDER_PAIRS * 2
            and NUMBER_OPEN_ORDER_PT == 0
        ):
            logging.info(f"Scenario 1b - Initial bot order state - No action")
            pass
        # 1c
        else:
            logging.info(f"Scenario 1c - Non-sense open orders - Cancel all")
            ws.cancel_all()
            place_order(current_position, IV_RANK)
    # Loop Scenario 2
    else:
        # 2a.1
        if NUMBER_OPEN_ORDER_MM == 0 and NUMBER_OPEN_ORDER_PT == 0:
            open_PT_order(current_position, IV_RANK)
            logging.info(
                f"Scenario 2a.1 - Open Positions = {CURRENT_SIZE} | MM order = {NUMBER_OPEN_ORDER_MM} |"
                f" PT order = {NUMBER_OPEN_ORDER_PT} | Placing PT order in opposite direction"
            )

        # 2b(s)
        elif NUMBER_OPEN_ORDER_PT == 0:
            if CURRENT_SIZE > 0 and NUMBER_OPEN_ORDER_MM_BUY != 0:
                ws.cancel_all()
                open_PT_order(current_position, IV_RANK)
                place_order(current_position, IV_RANK, ORDER_RESTRICITION="BUY_ONLY")
                logging.info(
                    f"Scenario 2b - Open Positions = {CURRENT_SIZE} | MM order = {NUMBER_OPEN_ORDER_MM} | PT Orders = {NUMBER_OPEN_ORDER_PT} - Cancel MM orders and place PT order in opposite direction"
                )

            elif CURRENT_SIZE < 0 and NUMBER_OPEN_ORDER_MM_SELL != 0:
                ws.cancel_all()
                open_PT_order(current_position, IV_RANK)
                place_order(current_position, IV_RANK, ORDER_RESTRICITION="SELL_ONLY")
                logging.info(
                    f"Scenario 2b - Open Positions = {CURRENT_SIZE} | MM order = {NUMBER_OPEN_ORDER_MM} |"
                    f"PT Orders = {NUMBER_OPEN_ORDER_PT} - Cancel MM orders and place PT order in opposite direction"
                )

        # 2c(1, 2, 3)
        elif NUMBER_OPEN_ORDER_MM_BUY != 0 and NUMBER_OPEN_ORDER_MM_SELL == 0:
            if CURRENT_SIZE > 0:
                pass

            elif CURRENT_SIZE < 0:
                ws.cancel_by_label(LABEL_MM + "_buy")
                place_order(current_position, IV_RANK, ORDER_RESTRICITION="SELL_ONLY")

            ws.cancel_by_label("Profit_taking")
            open_PT_order(current_position, IV_RANK)

            logging.info(
                f"Scenario 2c - Open Positions = {CURRENT_SIZE} | MM order = {NUMBER_OPEN_ORDER_MM} | "
                f"PT Orders = {NUMBER_OPEN_ORDER_PT} - Cancel PT order and place PT order in opposite direction"
            )

        # 2c(4, 5, 6)
        # @TODO: Review this scenario
        elif NUMBER_OPEN_ORDER_MM_BUY == 0 and NUMBER_OPEN_ORDER_MM_SELL != 0:
            if CURRENT_SIZE > 0:
                ws.cancel_by_label(LABEL_MM + "_sell")
                place_order(current_position, IV_RANK, ORDER_RESTRICITION="BUY_ONLY")

            else:
                ws.cancel_all()
                open_PT_order(current_position, IV_RANK)
                place_order(current_position, IV_RANK, ORDER_RESTRICITION="SELL_ONLY")

            logging.info(
                f"Scenario 2c(4, 5, 6) - Open Positions = {CURRENT_SIZE} | MM order = {NUMBER_OPEN_ORDER_MM} | "
                f"PT Orders = {NUMBER_OPEN_ORDER_PT} - Cancel PT order and place PT order in opposite direction"
            )

        # 2c(7, 8, 9, 10, 11, 12)
        elif NUMBER_OPEN_ORDER_MM_BUY != 0 and NUMBER_OPEN_ORDER_MM_SELL != 0:
            # 2c(7, 8, 9)
            if CURRENT_SIZE > 0:
                ws.cancel_all()
                open_PT_order(current_position, IV_RANK)
                place_order(current_position, IV_RANK, ORDER_RESTRICITION="BUY_ONLY")

                logging.info(
                    f"Scenario 2c(7, 8, 9) - Open Positions = {CURRENT_SIZE} | MM order = {NUMBER_OPEN_ORDER_MM} | "
                    f"PT Orders = {NUMBER_OPEN_ORDER_PT} - Cancel PT order and place PT order in opposite direction"
                )

            # 2c(10, 11, 12)
            elif CURRENT_SIZE < 0:
                ws.cancel_all()
                open_PT_order(current_position, IV_RANK)
                place_order(current_position, IV_RANK, ORDER_RESTRICITION="SELL_ONLY")
                logging.info(
                    f"Scenario 2c(10, 11, 12) - Open Positions = {CURRENT_SIZE} | MM order = {NUMBER_OPEN_ORDER_MM} | "
                    f"PT Orders = {NUMBER_OPEN_ORDER_PT} - Cancel PT order and place PT order in opposite direction"
                )

        # 2d(1, 2, 3)
        elif NUMBER_OPEN_ORDER_MM == 0 and NUMBER_OPEN_ORDER_PT != 0:
            ws.cancel_by_label("Profit_taking")
            open_PT_order(current_position, IV_RANK)

            if CURRENT_SIZE > 0:
                place_order(current_position, IV_RANK, ORDER_RESTRICITION="BUY_ONLY")
            elif CURRENT_SIZE < 0:
                place_order(current_position, IV_RANK, ORDER_RESTRICITION="SELL_ONLY")

            logging.info(
                f"Scenario 2d - Open Positions = {CURRENT_SIZE} | MM order = {NUMBER_OPEN_ORDER_MM} | "
                f"PT Orders = {NUMBER_OPEN_ORDER_PT} - Cancel PT order and place PT order in opposite direction"
            )

    return


def cancel_bot_orders(LABEL_MM):
    ws.cancel_by_label(LABEL_MM + "_buy")
    ws.cancel_by_label(LABEL_MM + "_sell")
    ws.cancel_by_label("Profit_taking")

    return


def has_position_changed(ws, SYMBOL, position_out):
    current_position = ws.get_position(SYMBOL)

    if position_out == {} or (
        current_position["average_price"] != position_out["average_price"]
        or current_position["size"] != position_out["size"]
    ):
        return True, current_position

    return False, current_position


def has_order_changed(ws, CURRENCY, last_time_out, NUMBER_OPEN_ORDER_MM_OUT):
    current_orders = ws.get_open_orders_by_currency(CURRENCY)

    if len(current_orders["result"]) != NUMBER_OPEN_ORDER_MM_OUT:
        return True

    # Check if there has been a change in orders
    if any(
        order["last_update_timestamp"] > last_time_out
        for order in current_orders["result"]
    ):
        return True

    return False


def get_position(ws):
    # get account summary
    current_position = ws.get_position(SYMBOL)

    return current_position


"""
###############################################################################
Innitialize the BOT
---------------------

The steps to initialize the bot are:
    1. Connect to the deribit api
    2. Calculate IV Rank
    3. Handle for open position 
    4. Handle PT standing orders

###############################################################################
"""

# 1. Connect to the deribit api
ws = connect_deribit()

# # 2. run IV RANK Function
IV_RANK = vol.get_iv_rank(
    ws,
    CURRENCY,
    DAYS,
    END_DATE_IV_RANK,
    RESOLUTION=RESOLUTION,
)


# Initialize the variables
CURRENT_TIME = END_DATE_IV_RANK

counter = 0  # Display purposes only

position_out = {}

# save the current time in millesecond EPOX unixtime
LAST_TIME_OUT = ws.get_time()
LAST_TIME_OUT = LAST_TIME_OUT["result"]
NUMBER_OPEN_ORDER_MM_OUT = 0

logging.info(f"Bot is running... ")


""""
Run an infinite loop
"""
while True:
    # if the bot is not connected, then the bot will reconnect
    # otherwise the bot reconnect to the deribit api
    response = ws.test_creds()
    if "error" in response.keys():
        ws = connect_deribit()
        logging.info("Error found: on line If error in response.key()", response)

    # check if there has been any change in orders (amount, price, etc)
    result_position_change, current_position = has_position_changed(
        ws, SYMBOL, position_out
    )
    if result_position_change == True:
        logging.info(f"Position has changed")

    result_order_change = has_order_changed(
        ws, CURRENCY, LAST_TIME_OUT, NUMBER_OPEN_ORDER_MM_OUT
    )
    if result_order_change == True:
        logging.info(f"Order has changed")
    else:
        logging.info(f"No change in orders")

    if result_position_change == True or result_order_change == True:
        # current_position = ws.get_position(SYMBOL)

        open_orders_mm_buy, open_orders_mm_sell, open_orders_pt = get_open_orders(
            "BTC", LABEL_MM + "_buy", LABEL_MM + "_sell", "Profit_taking"
        )

        # check if IV Rank needs to be updated. It should be updated every day
        IV_RANK, END_DATE_IV_RANK = calculate_iv_rank(
            IV_RANK,
            END_DATE_IV_RANK,
            CURRENCY,
            DAYS,
            RESOLUTION,
            IV_RANK_FREQ_UPADATE,
            CURRENCY,
            SYMBOL,
        )

        # checks in which scenario the bot is
        CURRENT_SCENARIO = position_scenario(
            current_position,
            open_orders_mm_buy,
            open_orders_mm_sell,
            open_orders_pt,
        )

        position_out = ws.get_position(SYMBOL)

        LAST_TIME_OUT = ws.get_time()
        LAST_TIME_OUT = LAST_TIME_OUT["result"]

        # get open orders mm
        open_orders_mm_buy, open_orders_mm_sell, open_orders_pt = get_open_orders(
            CURRENCY, LABEL_MM + "_buy", LABEL_MM + "_sell", "Profit_taking"
        )

        NUMBER_OPEN_ORDER_MM_OUT = len(
            open_orders_mm_buy + open_orders_mm_sell + open_orders_pt
        )
        if open_orders_pt and len(open_orders_pt) > 0:
            # Access the first element in the list
            print(
                f"Current PT price: {open_orders_pt[0]['price']} and amount: {open_orders_pt[0]['amount']}"
            )
        else:
            print("open_orders_pt is empty or has no elements")

        for i in range(len(open_orders_mm_buy)):
            logging.info(
                f"Current MM buy price: {open_orders_mm_buy[i]['price']} and amount: {open_orders_mm_buy[i]['amount']}"
            )

    logging.info(f"The bot is waiting for the next run...")
    counter += 1
    time.sleep(60)
