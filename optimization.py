from io import BytesIO # to overcome streamlit problem
# with matplotlib pyplot displays to a max width
# in efficient frontier plotting

# import plotly.tools as tls # again for 
# # efficient frontier plotting but converting
# # matplotlib fig to plotly

import copy
import time
import datetime as dt

import streamlit as st

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

import pandas_datareader as pdr
import yfinance as yf

from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt import plotting
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices



# ================================================
# main function
# ================================================    

def app(tickers):
    # ================================================
    # Выбор дат, цели оптимизации и доп аргументов
    # ================================================    

    config_container = st.container()
    with config_container:
        # show debug info
        st.checkbox('Show debug info',key='debug_info')

        # поле ввода цели оптимизации и доп аргументов
        col3,col4,_,_ = st.columns(4)

        col3.selectbox('Optimization target',
                       ['Max Sharpe',
                        'Efficient risk',
                        'Efficient return',
                        'Minimum volatility'],
                       key='optimization_target_select_box')

        risk_free_rate = col4.number_input('Risk free rate',
                                       value=st.session_state['risk_free_rate'],
                                       key='risk_free_rate',
                                        step=0.001)


        additional_parameters = st.container()

        with additional_parameters:
            col5,col6,_,_ = st.columns(4)
            
            amount_to_invest = col5.number_input('Amount to invest',
                                                 min_value=0,
                                                 step=0,
                                                 value=20000,
                                                 key='amount_to_invest')

            if st.session_state['optimization_target_select_box'] == 'Efficient risk':
                target_volatility = col6.number_input('Target volatility',
                                                      value=st.session_state['target_volatility'],
                                                      key='target_volatility',
                                                      step=0.001,
                                                      format='%f')

            elif st.session_state['optimization_target_select_box'] == 'Efficient return':
                target_return = col6.number_input('Target return',
                                                  value=st.session_state['target_return'],
                                                  key='target_return',
                                                  step=0.001,
                                                  format='%f')

            elif st.session_state['optimization_target_select_box'] == 'Minimum volatility':
                pass



    # ================================================
    # Запуск оптимизатора
    # ================================================
    
    if st.button('Optimize'):
        
        # Загрузка ценовой истории выбранных тикеров
            try:
                df = yf.download(st.session_state['tickers_in_portfolio'])['Adj Close']
                
                if st.session_state['debug_info'] == True:
                    st.write(df.head())
            except:
                pass

            # if st.session_state['show_more'] == True:    
            #     df

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
                    #########
                    # calculate expected return and cov matrix
                    #########                    
                    mu = expected_returns.mean_historical_return(df)
                    Sigma = risk_models.sample_cov(df)
                    
                    if st.session_state['debug_info'] == True:
                        mu
                        Sigma
                    
                    #########
                    # plot Efficient Frontier
                    #########
                    st.title('Efficient frontier chart')    
                    
                    ef_plotting = EfficientFrontier(mu, Sigma)
                    
                    fig, ax = plt.subplots(figsize=(4, 4))
                    plotting.plot_efficient_frontier(ef_plotting, ax=ax, show_assets=True)
                    # plt.show()
                    # st.pyplot(fig)
                    
                    # save fig to file
                    # and load as image
                    buf = BytesIO()
                    fig.savefig(buf, format="png")
                    st.image(buf)
                    
                    # plotly_fig = tls.mpl_to_plotly(fig)
                    # st.plotly_chart(plotly_fig)
                    
                    #########
                    # compute efficient frontier with a target
                    #########
                    ef = EfficientFrontier(mu, Sigma)
                    
                    # calculate weights
                    if st.session_state['optimization_target_select_box'] == 'Max Sharpe':
                        weights = ef.max_sharpe(risk_free_rate)

                    elif st.session_state['optimization_target_select_box'] == 'Efficient risk':
                        weights = ef.efficient_risk(target_volatility)

                    elif st.session_state['optimization_target_select_box'] == 'Efficient return':
                        weights = ef.efficient_return(target_return)

                    elif st.session_state['optimization_target_select_box'] == 'Minimum volatility':
                        weights = ef.min_volatility()
                        
                    #########    
                    # plot weights
                    #########
                    st.title('Portfolio weights')    
                    fig,ax = plt.subplots()
                    plotting.plot_weights(weights,ax=ax)
                    buf = BytesIO()
                    fig.savefig(buf, format="png")
                    st.image(buf)

                    # get cleaned weights
                    if st.session_state['debug_info'] == True:
                        cleaned_weights = ef.clean_weights()                    
                        st.write(weights)
                        st.write(cleaned_weights)
                    
                    # calculate and display
                    # porfolio performance

                    expected_annual_return,annual_volatility,sharpe_ratio = ef.portfolio_performance(verbose=True, risk_free_rate = risk_free_rate)
                    
                    st.title('Portfolio performace')    
                    c1, c2, c3 = st.columns(3)
                    
                    c1.metric(label="Expected annual return", 
                              value=str(np.round(expected_annual_return,2)*100)+'%')
                    
                    c2.metric(label="Annual volatility", 
                              value=str(np.round(annual_volatility,2)*100)+'%')
                    
                    c3.metric(label="Sharpe ratio", 
                              value=np.round(sharpe_ratio,2))
                    
                    # calculate discrete allocation

                    latest_prices = get_latest_prices(df)
                    
                    if st.session_state['debug_info'] == True:
                        st.write(latest_prices)
                        
                    da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=amount_to_invest)
                    allocation, leftover = da.lp_portfolio()
                    if st.session_state['debug_info'] == True:
                        st.write(allocation)
                        st.write(leftover)
                    
                    st.title('Portfolio allocation')   
                    st.write(pd.DataFrame(allocation,index=['Number of shares']).T)
                    
                    


                except Exception as e:
                    st.write(e)
                    # pass
