import time

client_id = ""  # replace this with your key
# replace with your secret
client_secret = ""
live = False  # choice True or False. If True, the bot runs on the deribit api and if False, the bot runs on the

########################################################################################################################
# Target
########################################################################################################################

# Instrument to market make on BitMEX.
SYMBOL = "BTC-PERPETUAL"
########################################################################################################################
# Order Size & Spread
########################################################################################################################

# How many pairs of buy/sell orders to keep open
ORDER_PAIRS = 6

# ORDER_START_SIZE will be the number of contracts submitted on level 1
# Number of contracts from level 1 to ORDER_PAIRS - 1 will follow the function
# [ORDER_START_SIZE + ORDER_STEP_SIZE (Level -1)]
# ORDER_START_SIZE and ORDER_STEP_SIZE must be multiplication of instrument lot size.
ORDER_START_SIZE = 100
ORDER_STEP_SIZE = 0

# Distance between successive orders, as a percentage (example: 0.005 for 0.5%)
# INTERVAL = 0.01

interval_ranges = {
    (90, float("inf")): 0.02,
    (80, 90): 0.018,
    (70, 80): 0.016,
    (60, 70): 0.014,
    (50, 60): 0.010,
    (40, 50): 0.06,
    (30, 40): 0.004,
    (20, 30): 0.003,
    (10, 20): 0.002,
    (-float("inf"), 10): 0.0025,
}


# Interval between position is linear or geometrical increased?
INTERVAL_TYPE = "linear"  # "linear" or "geometrical"

# Determines whether the buy or sell is closer to the mid price
# If bullish, buy is closer to the mid price
# If bearish, sell is closer to the mid price
# If neutral, buy and sell are equidistant from the mid price
SKEW = "Bullish"  # "Bullish" or "Bearish" or "Neutral"

# Orders label
LABEL_MM = "MM"

########################################################################################################################
# IV RANK Variables
########################################################################################################################
# initiate the variables
CURRENCY = "BTC"
INDEX_NAME = "btc_usd"

# Number of days you want to subtract from the end date
DAYS = 30

# resolution of the data to calculate volatility in seconds
# options are: 1, 60. 3600, 43200, 1D
RESOLUTION = 3600
IV_RANK_FREQ_UPADATE = 1  # in hours

# Calculate the end date as the current date and time in UNIX Epoch time (milliseconds)
END_DATE_IV_RANK = int(time.time() * 1000)

########################################################################################################################
# Profit ranges
########################################################################################################################

# Define a dictionary for IV_RANK ranges and their corresponding PROFIT values
profit_ranges = {
    (90, float("inf")): 0.05,
    (80, 90): 0.045,
    (70, 80): 0.04,
    (60, 70): 0.035,
    (50, 60): 0.03,
    (40, 50): 0.015,
    (30, 40): 0.005,
    (0, 30): 0.0025,
    # (10, 20): 0.01,
    # (-float('inf'), 10): 0.005
}
