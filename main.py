import time
import datetime as dt

import streamlit as st

import numpy as np
import pandas as pd

import pandas_datareader as pdr
import yfinance as yf

from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns


# '''
# 1. Выбра

# '''

# ================================================
# Отладочная инфа  
# ================================================
# 'Отладочная инфа'
# st.session_state 

# ================================================
# Инициализация сессионных переменных
# ================================================

default_session_state_dict = {'disclaimer' :False,
                              'start_date': dt.date(2000,1,1),
                              'end_date': dt.datetime.now().date(),
                              'selected_tickers': [],
                              'risk_free_rate': 0.02,
                              'target_volatility': 0.02,
                              'target_return': 0.02,
                             }

for key,value in default_session_state_dict.items():
    if key not in st.session_state:
        st.session_state[key] = value
                              
    
# ================================================
# callback функции для изменения session_state
# ================================================    
def change_start_date():
    st.session_state['start_date'] = st.session_state['start_date_input']
    pass 

def change_end_date():
    st.session_state['end_date'] = st.session_state['end_date_input']    
    pass 

def change_risk_free_rate():
    st.session_state['risk_free_rate'] = st.session_state['risk_free_rate_input']
    pass

def change_target_volatility():
    st.session_state['target_volatility'] = st.session_state['target_volatility_input']
    pass

def change_target_return():
    st.session_state['target_return'] = st.session_state['target_return_input']
    pass

# ================================================
# Предзагрузка тикеров
# ================================================
# Cols description
# http://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs

df_tickers = pdr.nasdaq_trader.get_nasdaq_symbols(retry_count=3, timeout=30, pause=None)

mask = ((df_tickers['Financial Status'] == 'N')&
        (df_tickers['ETF'] == False)&
        (df_tickers['Market Category'] == 'Q')&
        (df_tickers['Test Issue'] == False)&
        (df_tickers['NextShares'] == False)&
        (df_tickers['Nasdaq Traded'] == True))

df_tickers = df_tickers.loc[mask]

tickers = df_tickers.index
    
# ================================================    
# Дисклеймер: кнопка, текст и таймер
# ================================================
# buff,buff,col1 = st.columns([2,2,1])    
# with col1:
#     if st.button('Disclaimer'):
#         st.session_state['disclaimer'] = True
    
# disclaimer_container = st.container()    
# if st.session_state['disclaimer']:
#     disclaimer_container.write('Тут дисклеймер')
#     st.session_state['disclaimer'] = False
#     my_bar = disclaimer_container.progress(0)

#     for percent_complete in range(100):
#         time.sleep(0.1)
#         my_bar.progress(percent_complete + 1)
        
#     st.experimental_rerun()
# else:
#     disclaimer_container.write()    
    
# ================================================
# Выбор дат, цели оптимизации и доп аргументов
# ================================================    
config_container = st.container()
with config_container:
    # поле ввода дат
    col1,col2 = st.columns(2)
    start_date = col1.date_input('Start date',
                               value=st.session_state['start_date'],
                               key='start_date_input',
                               on_change=change_start_date)
    
    end_date = col2.date_input('End date',
                             value=st.session_state['end_date'],
                             key='end_date_input',
                             on_change=change_end_date)
    
    # поле ввода цели оптимизации и доп аргументов
    col3,col4 = st.columns(2)
    
    col3.selectbox('Optimization target',
                   ['Max Sharpe',
                    'Efficient risk',
                    'Efficient return',
                    'Minimum volatility'],
                   key='optimization_target_select_box')
    
    risk_free_rate = col4.number_input('Risk free rate',
                                   value=st.session_state['risk_free_rate'],
                                   key='risk_free_rate_input',
                                   on_change=change_risk_free_rate,
                                    step=0.001)
                                       
    
    additional_parameters = st.container()
    
    with additional_parameters:
        col5,col6 = st.columns(2)
        
        if st.session_state['optimization_target_select_box'] == 'Efficient risk':
            target_volatility = col6.number_input('Target volatility',
                                                  value=st.session_state['target_volatility'],
                                                  key='target_volatility_input',
                                                  on_change=change_target_volatility,
                                                  step=0.001,
                                                  format='%f')

        elif st.session_state['optimization_target_select_box'] == 'Efficient return':
            target_return = col6.number_input('Target return',
                                              value=st.session_state['target_return'],
                                              key='target_return_input',
                                              on_change=change_target_return,
                                              step=0.001,
                                              format='%f')

        elif st.session_state['optimization_target_select_box'] == 'Minimum volatility':
            pass
    
# ================================================
# Выбор тикеров для портфолио    
# ================================================
tickers_container = st.container()
with tickers_container:
    
    if st.button('Generate random 5'):
        st.session_state['selected_tickers'] = np.random.choice(tickers.values,5)
                
    tickers_selection = st.multiselect('Select up to 10 NASDAQ Tickers',
                                       options=tickers,
                                       default=st.session_state['selected_tickers'],
                                       max_selections=10)
    
    st.checkbox('Show more securities info',key='show_more',value=False)
    
    if st.session_state['show_more'] == True:
        st.table(df_tickers.loc[tickers_selection,'Security Name'])

# ================================================
# Загрузка ценовой истории выбранных тикеров
# ================================================
    try:
        df = yf.download(tickers_selection)['Adj Close']
    except:
        pass
    
    if st.session_state['show_more'] == True:    
        df

# ================================================
# Загрузка цен в оптимизатор ---------------------
# ================================================

# Пояснение
    '''
    Mean-variance optimization requires two things: the expected returns of the assets, and the covariance matrix (or more generally, a risk model quantifying asset risk).
    '''

# Calculate expected annualized returns and sample covariance
    with st.spinner('Calculating...'):
        try:
            mu = expected_returns.mean_historical_return(df)
            Sigma = risk_models.sample_cov(df)

            # mu
            # Sigma

            # Obtain the EfficientFrontier
            ef = EfficientFrontier(mu, Sigma)

            st.session_state['optimization_target_select_box']

            # Select a chosen optimal portfolio
            if st.session_state['optimization_target_select_box'] == 'Max Sharpe':
                ef.max_sharpe(risk_free_rate)

            elif st.session_state['optimization_target_select_box'] == 'Efficient risk':
                ef.efficient_risk(target_volatility)

            elif st.session_state['optimization_target_select_box'] == 'Efficient return':
                ef.efficient_return(target_return)

            elif st.session_state['optimization_target_select_box'] == 'Minimum volatility':
                ef.min_volatility()


            expected_annual_return,annual_volatility,sharpe_ratio = ef.portfolio_performance(verbose=True, risk_free_rate = risk_free_rate)

            st.metric(label="expected_annual_return", value=expected_annual_return)
            st.metric(label="annual_volatility", value=annual_volatility)
            st.metric(label="sharpe_ratio", value=sharpe_ratio)

        except Exception as e:
            st.write(e)
            # pass