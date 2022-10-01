# This is the file which determines the layout/look of your webpage

# Import packages

import datetime as dt # pip install datetime
import numpy as np # pip install numpy
import pandas as pd  # pip install pandas
import plotly.graph_objs as go  # pip install plotly
import streamlit as st  # pip install streamlit
import streamlit_authenticator as stauth  # pip install streamlit-authenticator
from tradestation import *

# Set page config

st.set_page_config(page_title="Gamma Bot", page_icon=":chart_with_upwards_trend:", layout="wide")
# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/

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
 
    # ---- SIDEBAR ----

    authenticator.logout("Logout", "sidebar")
    expirations = get_expirations_ts()
    page_options = ["Chart"]
    callput_options = ["Call", "Put"]
    indicator_options = ["Gamma", "Bid", "Ask"]
    with st.sidebar:

        st.title(f"Welcome {name}")

        selected_side = st.selectbox(
            label = "Select Page:", 
            options = page_options
        )
        
        if selected_side == "Chart":
            selected_ticker = st.text_input(
                label = "Ticker:",
                value = "SPY"
            )
            selected_callput = st.radio(
                label = "Type:",
                options = callput_options,
                index = 0
            )
            selected_expiration = st.selectbox(
                label = "Expiration:", 
                index = 0,
                options = expirations
            )
            selected_indicators = st.multiselect(
                label = "Indicators:",
                options = indicator_options,
                default = "Gamma"
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

        # Get chain and sort by strikes

        chain = get_chain_ts(selected_ticker, selected_expiration, selected_callput)
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

        # Create Plotly chart from TDA market data

        fig = go.Figure()

        for indicator in selected_indicators:
            y_values = [float(item[indicator]) for item in chain]
            fig.add_trace(go.Scatter(
                x = pd.Series(strikes),
                y = pd.Series(y_values),
                name = indicator,
            ))
        # fig.add_vline(x=last, annotation="Last")
        fig.update_layout(
            title = f'Plotly chart: {selected_ticker} ({last}), {selected_callput} chain for {selected_expiration} expiration date',
            height = 700,
            yaxis_title = indicator,
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