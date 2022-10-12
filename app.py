# This is the file which determines the layout/look of your webpage

# Import packages

import datetime as dt # pip install datetime
import numpy as np # pip install numpy
import pandas as pd  # pip install pandas
import plotly.graph_objs as go  # pip install plotly
import pytz
import streamlit as st  # pip install streamlit
from streamlit_autorefresh import st_autorefresh # pip install streamlit-autorefresh
import streamlit_authenticator as stauth  # pip install streamlit-authenticator
import time
from tradestation import *

# Set page config

st.set_page_config(page_title="Gamma Bot", page_icon=":chart_with_upwards_trend:", layout="wide")
# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/

# Global variables

utc = pytz.timezone("UTC")
local_timezone = pytz.timezone("US/Central")

# Database connection

deta = connect_db()
users_db = deta.Base("users_db")

# User login

users = users_db.fetch().items
usernames = [user["key"] for user in users]
names = [user["name"] for user in users]
hashed_passwords = [user["password"] for user in users]
authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "sales_dashboard", "abcdef", cookie_expiry_days=30)
name, auth, username = authenticator.login("Login", "main")
if auth == False:
    st.error("Username/password is incorrect")
if auth == None:
    st.warning("Please enter your username and password")

# Main page after login

if auth:

    # Remove whitespace from the top of the page and sidebar

    whitespace_style = \
        """
        <style>
            .css-18e3th9 {
                    padding-top: 0rem;
                    padding-bottom: 10rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
            .css-1d391kg {
                    padding-top: 3rem;
                    padding-right: 1rem;
                    padding-bottom: 3rem;
                    padding-left: 1rem;
                }
            .css-hxt7ib {
                    padding-top: 3rem;
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
            .css-r4g17z {
                    height: 2rem;
                }
        </style>
        """
    st.markdown(whitespace_style, unsafe_allow_html=True)

    # Title of page

    st.title(":chart_with_upwards_trend: Gamma Bot")
    st.markdown("##")

    # Database connection (again)

    deta = connect_db()
    config_db = deta.Base("config_db")
    settings_db = deta.Base("settings_db")

    # Session state, and autorefresh

    if "ticker" not in st.session_state:
        st.session_state["ticker"] = settings_db.get("TICKER")['value']
    if "refresh_str" not in st.session_state:
        refresh_bool = bool(settings_db.get("REFRESH_ON")['value'])
        if refresh_bool:
            refresh_str = "On"
        else:
            refresh_str = "Off"
        st.session_state["refresh_str"] = refresh_str
    if "refresh_seconds" not in st.session_state:
        st.session_state["refresh_seconds"] = int(settings_db.get("REFRESH_SECONDS")['value'])
    if "refresh_str_input" in st.session_state and "refresh_seconds_input" in st.session_state:
        if st.session_state["refresh_str_input"] == "On":
            count = st_autorefresh(interval=st.session_state["refresh_seconds_input"]*1000, limit=1000, key="refresh_counter")
    elif "refresh_str_input" in st.session_state:
        if st.session_state["refresh_str_input"] == "On":
            count = st_autorefresh(interval=st.session_state["refresh_seconds"]*1000, limit=1000, key="refresh_counter")
    elif "refresh_seconds_input" in st.session_state:
        if st.session_state["refresh_str"] == "On":
            count = st_autorefresh(interval=st.session_state["refresh_seconds_input"]*1000, limit=1000, key="refresh_counter")
    else:
        if st.session_state["refresh_str"] == "On":
            count = st_autorefresh(interval=st.session_state["refresh_seconds"]*1000, limit=1000, key="refresh_counter")
    if "ticker_input" not in st.session_state:
        expirations = get_expirations_ts(st.session_state["ticker"])
    else:
        expirations = get_expirations_ts(st.session_state["ticker_input"])
    start_local = pd.Timestamp(time.time(), unit="s", tz=utc).astimezone(local_timezone)
    time_cutoff = dt.datetime(year=start_local.year, month=start_local.month, day=start_local.day, hour=15, minute=1)
    time_cutoff = pd.Timestamp(time_cutoff, tz=local_timezone)
    if start_local > time_cutoff and expirations[0] == start_local.strftime("%m-%d-%Y"):
        exp_idx = 1
    else:
        exp_idx = 0

    # Callback functions

    def change_ticker():
        entry = {}
        entry["key"] = "TICKER"
        entry["value"] = st.session_state["ticker_input"]
        print(entry)
        settings_db.put(entry)

    def change_refresh_on():
        entry = {}
        entry["key"] = "REFRESH_ON"
        if st.session_state["refresh_str_input"] == "On":
            entry["value"] = True
        elif st.session_state["refresh_str_input"] == "Off":
            entry["value"] = False
        print(entry)
        settings_db.put(entry)

    def change_refresh_seconds():
        entry = {}
        entry["key"] = "REFRESH_SECONDS"
        entry["value"] = st.session_state["refresh_seconds_input"]
        print(entry)
        settings_db.put(entry)

    # ---- SIDEBAR ----

    authenticator.logout("Logout", "sidebar")
    page_options = ["Chart"]
    callput_options = ["Call", "Put", "All"]
    indicator_options = ["Ask", "Bid", "DailyOpenInterest", "Delta", "Delta Indicator", "Gamma", "Gamma Indicator", 
                         "ImpliedVolatility", "Mid", "Rho", "Theta", "Vega", "Volume"]
    complex_indicators = ["Gamma Indicator", "Delta Indicator"]
    refresh_options = ["On", "Off"]

    with st.sidebar:

        # st.title(f"Welcome {name}")

        selected_side = st.selectbox(
            label = "Select Page:", 
            options = page_options
        )
        
        if selected_side == "Chart":
            selected_ticker = st.text_input(
                label = "Ticker:",
                value = st.session_state["ticker"],
                on_change = change_ticker,
                key = "ticker_input"
            )
            selected_callput = st.radio(
                label = "Type:",
                options = callput_options,
                index = 2,
                horizontal = True,
            )
            selected_expiration = st.selectbox(
                label = "Expiration:", 
                index = exp_idx,
                options = expirations
            )
            selected_indicators = st.multiselect(
                label = "Indicators:",
                options = indicator_options,
                default = "Gamma Indicator"
            )
            selected_refresh_on = st.radio(
                label = "Auto-refresh:",
                options = refresh_options,
                index = refresh_options.index(st.session_state["refresh_str"]),
                on_change = change_refresh_on,
                horizontal = True,
                key = "refresh_str_input"
            )
            selected_refresh_seconds = st.number_input(
                label = "Auto-refresh seconds:",
                min_value = 0,
                value = st.session_state["refresh_seconds"],
                step = 1,
                on_change = change_refresh_seconds,
                key = "refresh_seconds_input"
            )

    # Chart page

    if selected_side == "Chart":

        # Get quote

        selected_ticker = selected_ticker.upper()
        quote = get_quote_ts(selected_ticker)
        last = str(np.round(float(quote['Last']), 2))
        if "." not in last:
            last = last + ".00"
        if len(last.split(".")[1]) == 1:
            last = last + "0"

        # Create Plotly chart from TDA market data

        fig = go.Figure()

        # Get chain, sort by strikes, add to figure

        chains = get_chain_ts(selected_ticker, selected_expiration, selected_callput)
        calls = chains['calls']
        puts = chains['puts']
        callputs = [calls, puts]
        count = 0
        ext = "Call"
        for chain in callputs:
            if count == 1:
                ext = "Put"
            if chain != []:
                strikes = [float(item['Strikes'][0]) for item in chain]
                strikes_enum = [strike for strike in enumerate(strikes)]
                strikes_enum_rev = [tuple(reversed(strike)) for strike in strikes_enum]
                strikes_enum_rev_sort = sorted(strikes_enum_rev)
                strikes = [strike[0] for strike in strikes_enum_rev_sort]
                strikes_idx = [strike[1] for strike in strikes_enum_rev_sort]
                chain1 = []
                for i in range(len(chain)):
                    strike1 = chain[strikes_idx[i]]
                    chain1.append(strike1)
                chain = chain1
                for indicator in selected_indicators:
                    y_values = []
                    if indicator not in complex_indicators:
                        y_values = [float(item[indicator]) for item in chain]
                    elif indicator in ["Gamma Indicator", "Delta Indicator"]:
                        if calls != [] and puts != []:
                            gammas = np.array([float(item["Gamma"]) for item in chain])
                            deltas = np.array([float(item["Delta"]) for item in chain])
                            volumes = np.array([float(item["Volume"]) for item in chain])
                            ois = np.array([float(item["DailyOpenInterest"]) for item in chain])
                            if count == 0:
                                gammas_call = gammas.copy()
                                deltas_call = deltas.copy()
                                volumes_call = volumes.copy()
                                # ois_call = ois.copy()
                            elif count == 1:
                                gammas_put = gammas.copy()
                                deltas_put = deltas.copy()
                                volumes_put = volumes.copy()
                                # ois_put = ois.copy()
                                # y_values = (ois_call - ois_put) * gammas_call
                                if indicator == "Gamma Indicator":
                                    y_values = (volumes_call * gammas_call) - (volumes_put * gammas_put)
                                    st.info(f"{indicator} = (call volume * call gamma) - (put volume * put gamma)", icon="ℹ️")
                                elif indicator == "Delta Indicator":
                                    y_values = (volumes_call * deltas_call) - (volumes_put * deltas_put)
                                    st.info(f"{indicator} = (call volume * call delta) - (put volume * put delta)", icon="ℹ️")
                        else:
                            st.warning(f"{indicator} requires both calls and puts", icon="⚠️")
                    if list(y_values) != []:
                        fig.add_trace(go.Scatter(
                            x = pd.Series(strikes),
                            y = pd.Series(y_values),
                            name = f"{indicator}, {ext}",
                            line_shape="spline",
                        ))
            count += 1
        # fig.add_vline(x=last, annotation="Last")
        fig.update_layout(
            title = f'Plotly chart: {selected_ticker} ({last}), {selected_callput} chain for {selected_expiration} expiration date',
            height = 700,
            yaxis_title = str(selected_indicators),
            xaxis_title = 'Strike',
            plot_bgcolor = 'gainsboro',
            annotations=[dict(x=last, y=0.99, yref='paper', text='Last', xanchor='left', showarrow=False, font_color="red")],
            shapes=[dict(x0=last, x1=last, y0=0.01, y1 = 0.99, yref='paper', line_width=1, line_dash="dash", line_color="red")] 
        )
        fig.update_xaxes(
            rangeslider_visible=False,
            showgrid=False,
            tickprefix=" "
        )
        fig.update_yaxes(
            showgrid=False,
            ticksuffix=" "
        )
        st.plotly_chart(fig, use_container_width = True)

        time_now = dt.datetime.now(tz=local_timezone).strftime('%Y-%m-%d %X %Z')
        st.write(f"Last updated: {time_now}")

    # ---- HIDE STREAMLIT STYLE ----
    hide_st_style = \
        """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
        """
    st.markdown(hide_st_style, unsafe_allow_html=True)