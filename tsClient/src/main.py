# Import the TradeStation auth package
import requests
import json

import ts_py.auth as a

import tsclient.config as config

credentials = config.get_creds()

client = a.easy_client(credentials["client_key"],
                       credentials["client_secret"],
                       credentials["call_back_domain"], paper_trade=True)
client._token_validation()

# nclient = a.client_from_manual_flow(
#     credentials["client_key"], client_secret=credentials["client_secret"]
#                                     ,redirect_uri=credentials["call_back_domain"]
#                                     ,paper_trade=False)
# Call your endpoint
# Define the user_id
user_id = "3535293"

accounts = "SIM1972545X"

url = "https://sim-api.tradestation.com/v3/brokerage/accounts"

with open('ts_state.json') as f:
    ts_state = json.load(f)

headers = {"Authorization": f"Bearer {ts_state['access_token']}"}
response = requests.request("GET", url, headers=headers)
# print("response.text" + ts_state['access_token'])
print(response.text)


# symbol = ['spxw.x']

# symbols = client.get_symbol_details(symbol)
# print(symbols.content)
