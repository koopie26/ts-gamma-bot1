# This file creates several tables in our Deta base with the below default values; run only once

# Import packages

from db import *
import streamlit_authenticator as stauth
import os

# Connect to database

deta = connect_db()
config_db = deta.Base("config_db")
users_db = deta.Base("users_db")
settings_db = deta.Base("settings_db")

# Fetch existing entries in config_db and delete them

# items = config_db.fetch().items
# keys = [item['key'] for item in items]
# for key in keys:
#     config_db.delete(key)

# Fetch existing entries in users_db and delete them

# items = users_db.fetch().items
# keys = [item['key'] for item in items]
# for key in keys:
#     users_db.delete(key)

# Fetch existing entries in settings_db and delete them

# items = settings_db.fetch().items
# keys = [item['key'] for item in items]
# for key in keys:
#     settings_db.delete(key)

# Setup user database

usernames = ["mark", "tyler"]
names = ["Mark", "Tyler"]
passwords = ["tsbot", "gammabot"]
hashed_passwords = stauth.Hasher(passwords).generate() # Encrypt passwords

for i in range(len(usernames)):
    entry = {
        "key": usernames[i], 
        "name": names[i], 
        "password": hashed_passwords[i],
        # "password1": passwords[i],
    }
    users_db.put(entry)

# Setup config database

config_keys = ["DETA_KEY", "TS_ACCESS", "TS_ACCOUNT", "TS_API", "TS_REFRESH", "TS_SECRET", \
               "TS_SIM_EQUITY", "TS_SIM_FOREX", "TS_SIM_FUTURES", "TS_USERNAME"]
config_values = [os.getenv(key) for key in config_keys]
config_keys = config_keys + ["TS_TIME", "APPLY_REAL"]
config_values = config_values + ["8/8/2022 20:54:30", False]

for i in range(len(config_keys)):
    entry = {
        "key": config_keys[i],
        "value": config_values[i]
    }
    config_db.put(entry)

# Setup settings database

settings_keys = ["REFRESH_ON", "REFRESH_SECONDS", "TICKER"]
settings_values = [True, 60, "SPY"]

for i in range(len(settings_keys)):
    entry = {
        "key": settings_keys[i],
        "value": settings_values[i]
    }
    settings_db.put(entry)

# Finish

print("Deta updated")