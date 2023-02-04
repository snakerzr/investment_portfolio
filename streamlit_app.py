#######################
# Imports
#######################
import datetime as dt

# streamlit
import streamlit as st

# plotly
import plotly.io as pio

# pandas datareader to download tickers from nasdaq
import pandas_datareader as pdr

# analysis and portfolio optimization
import optimization as app1
import analytics as app2
# import app1
# import app2

#######################
# Configs
#######################
# plotly config
pio.renderers.default = 'browser'

# streamlit config
st.set_page_config(layout="wide")


# default session variables initialization
default_session_state_dict = {'disclaimer': False,
                              # 'start_date': dt.date(2000,1,1),
                              # 'end_date': dt.datetime.now().date(),
                              'selected_tickers_for_analytics': ['GOOG'],
                              'tickers_in_portfolio': [],
                              'risk_free_rate': 0.02,
                              'target_volatility': 0.02,
                              'target_return': 0.02,
                             }

for key,value in default_session_state_dict.items():
    if key not in st.session_state:
        st.session_state[key] = value
        
        
#######################
# Stuff to preload
#######################   

# get ticker names from NASDAQ as options for multiselect
df_tickers = pdr.nasdaq_trader.get_nasdaq_symbols(retry_count=3, timeout=30, pause=None)
# filter them out
mask = ((df_tickers['Financial Status'] == 'N') &
                (df_tickers['ETF'] == False) &
                (df_tickers['Market Category'] == 'Q') &
                (df_tickers['Test Issue'] == False) &
                (df_tickers['NextShares'] == False) &
                (df_tickers['Nasdaq Traded'] == True))

df_tickers = df_tickers.loc[mask]
# take only names
tickers = df_tickers.index        


#######################
# Sidebar
#######################       
# two pages
PAGES = {
    "Analytics": app2,
    "Portfolio Optimization": app1
}

st.sidebar.title('Navigation')
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page = PAGES[selection]
page.app(tickers)



# multiselect
tickers_selection = st.sidebar.multiselect('NASDAQ tickers in your portfolio',
                                           options=tickers, 
                                           max_selections=20, 
                                           # default=[], 
                                           key="tickers_in_portfolio")

# dates selection

# Note: I'm not sure whenever dates should be be used in optimization
# So they might appear only in analytics

# start_date = st.sidebar.date_input('Start date', dt.date(2000,1,1), key = 'start_date')
# end_date = st.sidebar.date_input('End date', dt.datetime.now().date(), key = 'end_date')

# start_date = st.sidebar.date_input('Start date', 
#                                    st.session_state['start_date'], 
#                                    key='start_date')
# end_date = st.sidebar.date_input('End date', 
#                                  st.session_state['end_date'], 
#                                  key='end_date')