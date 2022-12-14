# This file contains a function to connect to our Deta base

# Import required packages

from deta import Deta
from dotenv import load_dotenv
import os
import streamlit as st

# Connect to Deta Base

def connect_db():
    if ".env" in os.listdir():
        env = load_dotenv(".env")
        DETA_KEY = os.getenv("DETA_KEY")
    else:
        try:
            DETA_KEY = os.environ["DETA_KEY"]
        except KeyError:
            DETA_KEY = st.secrets["DETA_KEY"]
    deta = Deta(DETA_KEY)
    return deta