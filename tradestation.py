# This file contains TradeStation functions and a few helper functions

# Import required packages

import datetime as dt
from db import *
import json
import numpy as np
import pandas as pd
import pytz
import requests
import yfinance as yf

# Global variables

utc = pytz.timezone("UTC")
local_timezone = pytz.timezone("US/Central")
ts_api = ""
ts_secret = ""
ts_refresh = ""
apply_real = False
ts_base = ""
ts_account = 0

# Helper functions

def flatten(lst):
    for x in lst:
        if isinstance(x, list):
            for x in flatten(x):
                yield x
        else:
            yield x

def find_atm(lst, val):
    lst1 = []
    for item in lst:
        if type(item) == str:
            if "." in item:
                item = float(item)
            else:
                item = int(item)
            lst1.append(item)
    lst = lst1
    if type(val) == str:
        if "." in val:
            val = float(val)
        else:
            val = int(val)
    arr = np.array(lst)
    diffs = abs(arr - val)
    mini = min(diffs)
    idx = list(diffs).index(mini)
    atm = lst[idx]
    return atm

# Core functions

def ts_authenticate():

    # Global variables

    global ts_api
    global ts_secret
    global ts_refresh
    global apply_real
    global ts_base
    global ts_account

    # Connect to Deta-Base

    deta = connect_db()
    config_db = deta.Base("config_db")
    ts_api = config_db.get("TS_API")['value']
    ts_secret = config_db.get("TS_SECRET")['value']
    ts_refresh = config_db.get("TS_REFRESH")['value']
    apply_real = bool(config_db.get("APPLY_REAL")['value'])
    if apply_real:
        ts_base = 'https://api.tradestation.com'
        ts_account = config_db.get("TS_ACCOUNT")['value']
    else:
        ts_base = 'https://sim-api.tradestation.com'
        ts_account = config_db.get("TS_SIM_EQUITY")['value']

    # Extract info

    ts_refresh_data = { 
        'grant_type': 'refresh_token', 
        'client_id': ts_api, 
        'client_secret': ts_secret, 
        'refresh_token': ts_refresh 
    } 
    ts_token_url = "https://signin.tradestation.com/oauth/token" 
    ts_headers = {'content-type': 'application/x-www-form-urlencoded'}
    ts_limit = 20
    ts_limit_adj = int(ts_limit * 0.9)
    now_time = dt.datetime.now(local_timezone)
    config_db = connect_db().Base("config_db")
    ts_time = pd.Timestamp(config_db.get("TS_TIME")['value'], tz=local_timezone)
    minutes_since_refresh = round((now_time - ts_time).total_seconds() / 60, 2)
    if minutes_since_refresh > ts_limit_adj:
        r = requests.post(ts_token_url, data= ts_refresh_data, headers = ts_headers) 
        if r.status_code not in [200, 201]:
            print(r.content)
        ts_access_token = r.json()['access_token']
        put_keys = ["TS_ACCESS", "TS_TIME"]
        put_values = [ts_access_token, now_time.strftime("%Y-%m-%d %X")]
        for i in range(len(put_keys)):
            entry = {
                "key": put_keys[i],
                "value": put_values[i]
            }
            config_db.put(entry)
    else:
        ts_access_token = config_db.get("TS_ACCESS")['value']
    auth_headers = {"Authorization": f"Bearer {ts_access_token}"}
    return auth_headers

def get_expirations_ts(symbol="SPY"):
    headers = ts_authenticate()
    url = f'{ts_base}/v3/marketdata/options/expirations/{symbol}'
    r = requests.get(url, headers = headers)
    if r.status_code not in [200, 201]:
        print(r.content)
    content = json.loads(r.content)
    if "Expirations" not in content:
        print(content)
    exps = content["Expirations"]
    exp_dates = [pd.to_datetime(exp["Date"]).strftime("%m-%d-%Y") for exp in exps]
    return exp_dates

def get_strikes_ts(symbol="SPY", expiration=0):
    if not expiration:
        expiration = get_expirations_ts(symbol)[0]
        # expiration = "12-17-2021"
    headers = ts_authenticate()
    url = f'{ts_base}/v3/marketdata/options/strikes/{symbol}?expiration={expiration}'
    r = requests.get(url, headers = headers)
    if r.status_code not in [200, 201]:
        print(r.content)
    content = json.loads(r.content)
    if "Strikes" not in content:
        print(content)
    strikes = list(flatten(content["Strikes"]))
    return strikes

def get_quote_ts(symbol="SPY"):
    headers = ts_authenticate()
    url = f'{ts_base}/v3/marketdata/quotes/{symbol}'
    r = requests.get(url, headers = headers)
    if r.status_code not in [200, 201]:
        print(r.content)
    content = json.loads(r.content)
    if 'Quotes' not in content:
        print(content)
        backup_quote = {
            "Last": yf.Ticker(symbol).info['regularMarketPrice']
        }
        return backup_quote
    quotes = content['Quotes']
    if len(quotes) == 1:
        quote = quotes[0]
    return quote

def get_option_ts(option_symbol=0):
    # MSFT%20220916C305 or MSFT 220916C305
    if not option_symbol:
        exp = pd.to_datetime(get_expirations_ts()[0]).strftime("%y%m%d")
        atm = find_atm(get_strikes_ts(), get_quote_ts()['Last'])
        option_symbol = f"SPY {exp}C{atm}"
    headers = ts_authenticate()
    url = f'{ts_base}/v3/marketdata/stream/options/quotes'
    querystring = {
        "legs[0].Symbol": option_symbol
    }
    r = requests.request("GET", url, headers = headers, params = querystring, stream = True)
    for line in r.iter_lines():
        if line:
            line_json = json.loads(line)
            return line_json

def get_chain_ts(symbol="SPY", expiration=0, optionType="All", strikeProximity=20, enableGreeks=True):
    # optionType = All (default), Call, and Put
    # strikeRange = All (deault), ITM, and OTM
    if not expiration:
        expiration = get_expirations_ts(symbol)[0]
    headers = ts_authenticate()
    option_types = [optionType]
    if "All" in option_types:
        option_types = ["Call", "Put"]
    calls, puts = [], []
    for option_type in option_types:
        strikes = get_strikes_ts(symbol, expiration)
        url = f'{ts_base}/v3/marketdata/stream/options/chains/{symbol}?expiration={expiration}'
        url = f'{url}&strikeProximity={strikeProximity}&strikeRange=All&strikeInterval=2'
        url = f'{url}&optionType={option_type}&enableGreeks={enableGreeks}'
        r = requests.request("GET", url, headers = headers, stream=True)
        counter = 0
        for line in r.iter_lines():
            if line:
                line_json = json.loads(line)
                if len(calls) >= strikeProximity * 2 and option_type == "Call":
                    break
                elif len(puts) >= strikeProximity * 2 and option_type == "Put":
                    break
                elif "Heartbeat" in line_json:
                    break
                elif "Strikes" in line_json:
                    strike = line_json["Strikes"][0]
                    cp = line_json["Side"]
                    if strike in strikes:
                        if cp == "Call":
                            calls.append(line_json)
                        elif cp == "Put":
                            puts.append(line_json)
                        else:
                            print("Error: Neither Call nor Put")
                        strikes.remove(strike)
                        counter += 1
                else:
                    print(line_json)
    chain = {
        "calls": calls,
        "puts": puts
    }
    return chain

def get_bars_ts(symbol="SPY"):
    headers = ts_authenticate()
    today = dt.datetime.now(tz=local_timezone) - dt.timedelta(days=0)
    tz_offset = int(float(today.strftime("%z")) / 100)
    if tz_offset > 0:
        hour = 24 - tz_offset
    else:
        hour = abs(tz_offset)
    startdate_str = f"{today.year}-{today.month}-{today.day}T0{hour}:00:00Z"
    startdate = pd.to_datetime(startdate_str).astimezone(local_timezone)
    url = f'{ts_base}/v3/marketdata/barcharts/{symbol}?unit=Minute&interval=1&barsback=390'
    r = requests.request("GET", url, headers = headers)
    resp = json.loads(r.content)
    if 'Bars' not in resp:
        print("Error: Bars")
        return False
    bars = resp['Bars']
    timestamps = [pd.to_datetime(bar['TimeStamp']) for bar in bars]
    i = 0
    while i < len(timestamps):
        if timestamps[i] >= startdate:
            break
        i += 1
    bars = bars[i:]
    return bars

# END