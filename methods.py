import asyncio
import json

import websockets


class DeribitWS:

    def __init__(self, client_id, client_secret, live=False):

        if not live:
            self.url = 'wss://test.deribit.com/ws/api/v2'
        elif live:
            self.url = 'wss://www.deribit.com/ws/api/v2'
        else:
            raise Exception('live must be a bool, True=real, False=paper')

        self.client_id = client_id
        self.client_secret = client_secret

        self.auth_creds = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "public/auth",
            "params": {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
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
        if 'error' in response.keys():
            raise Exception(f"Auth failed with error {response['error']}")
        else:
            print("Auth creds are good, it worked")

    def sell(self, instrument, amount, type, label, price=0.00):
        if type == 'market':
            params = {
                "instrument_name": instrument,
                "amount": amount,
                "type": type,
                "label": label,
            }
        elif type == 'limit':
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

    def get_time(self):
        params = {
        }
        self.msg["method"] = "public/get_time"
        self.msg["params"] = params
        get_time = self.async_loop(self.pub_api, json.dumps(self.msg))

        return get_time

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
            "count": count
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
        params = {
            "currency": currency,
            "kind": kind,
            "expired": expired
        }

        self.msg["method"] = "public/get_instruments"
        self.msg["params"] = params
        resp = self.async_loop(self.pub_api, json.dumps(self.msg))
        instruments = [d["instrument_name"] for d in resp['result']]

        return instruments
