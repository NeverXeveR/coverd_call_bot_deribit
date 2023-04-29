# Title of the Project

 Covered Call Trading Bot on Deribit Exchange


## Bot Performance
If you would like to see the bot's performance, visit https://neverxever-streamlit-bot-main-nsxpem.streamlit.app/.
The bot is running since 01-Apr-2023 and during its first 10 days, it returned 400% more than BTC. 
When backtesting the bot on a period of 3 years, the bot would have returned 100% than BTC. 
For more details visit the wiki section of the bot's web app.

## Description

This is a Python trading bot that makes 1 trade per day on Deribit exchange, short selling the first Out-the-Money 
(OTM) BTC or ETH call with a market order and placing limit orders at the 3rd and 5th OTM calls (trailing order calls). 
The bot is designed to sell calls with 1 Day-to-expiration (1 DTE) options, and if the first OTM call ask is below a 
minimum sale price, then the bot places a limited order at a pre-set price. As the options expiration time is at 8:00 am UTC, the bot places an order every day at 8:05 am.

## Advantages of the Strategy

Because on Deribit, you deposit BTC/ETH instead of fiat currency, essentially, the bot trades covered calls by short 
selling a call against the BTC/ETH position. A covered call is a bullish strategy, and the goal is to keep the premium 
of the short sale of the call while BTC/ETH stays within a certain price range. Historically, the first OTM 1-DTE call 
trades between 0.75% and 1% of the BTC value. The goal is to sell these calls every day, capture between 200% and 
300% of BTC/ETH premium per year, and have BTC/ETH appreciate less than these.

## Bot Inputs

The user should provide the following inputs:

- client_id: the Deribit client ID for the user's account
- client_secret: the Deribit client secret for the user's account
- live: True of False, if False it runs on test.deribit.com and if True it runs on a live Deribit account
- amount: the number of call contracts to be sold. The amounts are increased in increments of 0.1 BTC
- trailing_price: These are the prices that the out-of-the-money call options should be sold for
- max_margin: the maximum margin threshold. If the current margin is above this threshold, then the bot does not place any trade.
- delta: the delta in percentage for the strike price. If the current BTC is at USD 30,000 and delta = 1%, then the strike price will be at least at 30,300 USD
- min_sale_price: min ask price that the bot will make a trade for the first OTM call. If the bidding price < min_sale_price, then the bot will place a limit order at trailing prices.
- currency: BTC or ETH

## How to run the Bot
Once you have plugged in your Deribit API credentials, run the trading_bot file. The bot runs every day at 8am UCT.
You can also set a pythonanywhere account and have a task to be scheduled to run every day at this time instead of 
having the bot constantly running on a server.


## Support
If you like the bot, support me:
- Buy me a coffee: https://www.buymeacoffee.com/neverxever
- BTC: bc1qdmf35xjmqv9qxrdcxggq0qtjhwf43npzj0mu0m
- ETH: 0xB1c39A1818baEc2b4219F4F78Cd9065B64b85EE9

