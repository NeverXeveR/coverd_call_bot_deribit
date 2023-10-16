import asyncio
import json

import websockets


class DeribitWS:
    def __init__(self, client_id, client_secret, live=False):
        if not live:
            self.url = "wss://test.deribit.com/ws/api/v2"
        elif live:
            self.url = "wss://www.deribit.com/ws/api/v2"
        else:
            raise Exception("live must be a bool, True=real, False=paper")

        self.client_id = client_id
        self.client_secret = client_secret

        self.auth_creds = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "public/auth",
            "params": {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        }
        self.test_creds()

        self.msg = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": None,
        }

    async def pub_api(self, msg):
        async with websockets.connect(self.url) as websocket:
            await websocket.send(msg)
            while websocket.open:
                response = await websocket.recv()
                return json.loads(response)

    async def priv_api(self, msg):
        async with websockets.connect(self.url) as websocket:
            await websocket.send(json.dumps(self.auth_creds))
            while websocket.open:
                response = await websocket.recv()
                await websocket.send(msg)
                response = await websocket.recv()
                break
            return json.loads(response)

    @staticmethod
    def async_loop(api, message):
        return asyncio.get_event_loop().run_until_complete(api(message))

    def test_creds(self):
        response = self.async_loop(self.pub_api, json.dumps(self.auth_creds))
        if "error" in response.keys():
            raise Exception(f"Auth failed with error {response['error']}")
        else:
            print("Auth creds are good, it worked")
        return response

    def sell(self, instrument, amount, type, label, price=0.00):
        if type == "market":
            params = {
                "instrument_name": instrument,
                "amount": amount,
                "type": type,
                "label": label,
            }
        elif type == "limit":
            params = {
                "instrument_name": instrument,
                "amount": amount,
                "type": type,
                "label": label,
                "price": price,
            }
        self.msg["method"] = "private/sell"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def buy(self, instrument, amount, type, label, price=0.00):
        if type == "market":
            params = {
                "instrument_name": instrument,
                "amount": amount,
                "type": type,
                "label": label,
            }
        elif type == "limit":
            params = {
                "instrument_name": instrument,
                "amount": amount,
                "type": type,
                "label": label,
                "price": price,
            }
        self.msg["method"] = "private/buy"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def get_open_orders_by_instrument(self, instrument, type):
        params = {
            "instrument_name": instrument,
            "type": type,
        }
        self.msg["method"] = "private/get_open_orders_by_instrument"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def get_open_orders_by_label(self, currency, label):
        params = {
            "currency": currency,
            "label": label,
        }
        self.msg["method"] = "private/get_open_orders_by_label"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def get_open_orders_by_currency(self, currency):
        params = {
            "currency": currency,
        }
        self.msg["method"] = "private/get_open_orders_by_currency"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def edit(self, order_id, amount=None, price=None):
        params = {
            "order_id": order_id,
            "amount": amount,
            "price": price,
        }
        self.msg["method"] = "private/edit"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def edit_by_label(self, instrument_name, label=None, amount=None, price=None):
        params = {
            "instrument_name": instrument_name,
            "label": label,
            "amount": amount,
            "price": price,
        }
        self.msg["method"] = "private/edit_by_label"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def cancel_by_label(self, label):
        params = {
            "label": label,
        }
        self.msg["method"] = "private/cancel_by_label"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def cancel_all(self):
        params = {}
        self.msg["method"] = "private/cancel_all"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def get_order_state(self, ORDER_ID):
        params = {
            "order_id": ORDER_ID,
        }
        self.msg["method"] = "private/get_order_state"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def get_index_price(self, index_name):
        params = {
            "index_name": index_name,
        }
        self.msg["method"] = "public/get_index_price"
        self.msg["params"] = params
        resp = self.async_loop(self.pub_api, json.dumps(self.msg))

        return resp

    def get_time(self):
        params = {}
        self.msg["method"] = "public/get_time"
        self.msg["params"] = params
        resp = self.async_loop(self.pub_api, json.dumps(self.msg))

        return resp

    def get_volatility_index_data(
        self, currency, start_timestamp, end_timestamp, resolution
    ):
        params = {
            "currency": currency,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "resolution": resolution,
        }
        self.msg["method"] = "public/get_volatility_index_data"
        self.msg["params"] = params
        resp = self.async_loop(self.pub_api, json.dumps(self.msg))

        return resp

    def get_index(self, currency):
        params = {
            "currency": currency,
        }
        self.msg["method"] = "public/get_index"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def ticker(self, instrument_name):
        params = {
            "instrument_name": instrument_name,
        }
        self.msg["method"] = "public/ticker"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def get_transaction_log(self, currency, start_timestamp, end_timestamp, count=100):
        params = {
            "currency": currency,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "count": count,
        }
        self.msg["method"] = "private/get_transaction_log"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def get_account_summary(self, currency, extended=True):
        params = {
            "currency": currency,
            "extended": extended,
        }
        self.msg["method"] = "private/get_account_summary"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp

    def available_instruments(self, currency, kind, expired=False):
        # function that returns the available instruments names in the format of
        # "CURRENCY-EXPIRING_DATE-STRIKE_PRICE-KIND"
        params = {"currency": currency, "kind": kind, "expired": expired}

        self.msg["method"] = "public/get_instruments"
        self.msg["params"] = params
        resp = self.async_loop(self.pub_api, json.dumps(self.msg))
        instruments = [d["instrument_name"] for d in resp["result"]]

        return instruments

    def get_position(self, instrument_name):
        """ "
        msg =
            {
            "jsonrpc" : "2.0",
            "id" : 404,
            "method" : "private/get_position",
            "params" : {
                "instrument_name" : "BTC-PERPETUAL"
            }
            }

            {
            "jsonrpc": "2.0",
            "id": 404,
            "result": {
                "average_price": 0,
                "delta": 0,
                "direction": "buy",
                "estimated_liquidation_price": 0,
                "floating_profit_loss": 0,
                "index_price": 3555.86,
                "initial_margin": 0,
                "instrument_name": "BTC-PERPETUAL",
                "interest_value" : 1.7362511643080387,
                "leverage": 100,
                "kind": "future",
                "maintenance_margin": 0,
                "mark_price": 3556.62,
                "open_orders_margin": 0.000165889,
                "realized_profit_loss": 0,
                "settlement_price": 3555.44,
                "size": 0,
                "size_currency": 0,
                "total_profit_loss": 0
            }
            }
        """
        params = {
            "instrument_name": instrument_name,
        }
        self.msg["method"] = "private/get_position"
        self.msg["params"] = params
        resp = self.async_loop(self.priv_api, json.dumps(self.msg))
        return resp["result"]
