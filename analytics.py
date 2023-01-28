import datetime as dt

import yfinance as yf
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = 'browser'

def app(tickers):
    # added preloaded tickers list
    # place imports outside of the function

    tickers_selection = st.multiselect('Select NASDAQ tickers for analytics',
                                       options=tickers, 
                                       max_selections=4, 
                                       default=st.session_state['selected_tickers_for_analytics'], 
                                       )

    
    try: # without 'try' there is an error
        start_date = st.session_state['start_date']
        end_date = st.session_state['end_date']
        df = yf.download(tickers_selection).reset_index()
        df.columns = df.columns.map(''.join)
        df = df.query(' Date <= @end_date and Date >= @start_date')   # this string brings an error
    except:
        # place an error print here
        pass
    
    # try:
    #     st.write(df.head())    
    # except:
    #     pass



# ================================================
## Daily cumulative return chart
# ================================================

    cumprod_container = st.container()
    with cumprod_container:
        df_cumprod = df.loc[:, df.columns.str.contains('Adj Close') | df.columns.str.contains('Date')]
        df_cumprod = df_cumprod.set_index('Date')
        df_cumprod = (df_cumprod.pct_change() + 1).cumprod()
        fig = go.Figure()
        for i in range(len(df_cumprod.columns)):
            fig.add_trace(go.Scatter(x=df_cumprod.index, y=df_cumprod.iloc[:, i],
                                              name=df_cumprod.columns[i].replace('Adj Close', '')))
        fig.update_layout(barmode='overlay', width=1400, height=500, title_text='Daily cumulative return chart')
        fig.update_traces(opacity=0.75)
        st.plotly_chart(fig)

    hist_container = st.container()
    with hist_container:
        df_close = df.loc[:, df.columns.str.contains('Adj Close')]
        df_close = df_close.pct_change()
        fig = go.Figure()
        for i in range(len(df_close.columns)):
            fig.add_trace(
                go.Histogram(x=df_close.iloc[:, i], name=df_close.columns[i].replace('Adj Close', ''), xbins=dict(
                    start=-1,
                    end=1,
                    size=0.005),
                             autobinx=False))

        # Overlay both histograms
        fig.update_layout(barmode='overlay', width=1400, height=500, title_text='Daily return histogram')
        # Reduce opacity to see both histograms
        fig.update_traces(opacity=0.75)
        st.plotly_chart(fig)

        dfd = df_close.describe([.025, .25, .5, .75, .975])
        dfk = df_close.kurtosis().rename('kurtosis')
        dfs = df_close.skew().rename('skew')
        dfd = dfd.T.join(dfk).join(dfs).drop('count', axis=1)
        dfd['range'] = dfd['max'] - dfd['min']
        dfd['IQR'] = dfd['75%'] - dfd['25%']
        dfd.index = [x.replace('Adj Close', '') for x in dfd.index]
        st.dataframe(dfd, width=1500)

        # ================================================
        # Построение свечек
        # ================================================

    candles_container = st.container()
    with candles_container:

        candles_selection = st.selectbox('Select candle time', ('day', 'week', 'month'))
        tickers_selection = sorted(tickers_selection)
        number = st.number_input('Insert a number of days for the window', min_value=10, max_value=1000, value=250,
                                 step=10)
        number = int(number)
        for i in range(len(tickers_selection)):

            df_ticker = df.loc[:, df.columns.str.contains(tickers_selection[i]) | df.columns.str.contains(
                'Date') | df.columns.str.contains('Open') | df.columns.str.contains('High') | df.columns.str.contains(
                'Close') | df.columns.str.contains('Low')]
            df_ticker.columns = [x.replace(tickers_selection[i], '') for x in df_ticker.columns]
            if candles_selection == 'day':
                fig = go.Figure(data=[go.Candlestick(x=df_ticker['Date'],
                                                     open=df_ticker['Open'], high=df_ticker['High'],
                                                     low=df_ticker['Low'], close=df_ticker['Close'])])

                fig.update_layout(xaxis_rangeslider_visible=False, width=1400, height=400,
                                  title_text=f'{tickers_selection[i]} candlestick {candles_selection} chart')
                st.plotly_chart(fig)
            elif candles_selection == 'month':
                df_ticker['month'] = df_ticker['Date'].apply(lambda dt: dt.replace(day=1))
                df_ticker = df_ticker.sort_values(by='Date')
                df_month = df_ticker.groupby('month').agg(
                    {'Open': 'first', 'Close': 'last', 'High': 'max', 'Low': 'min'}).reset_index()
                df_month.columns = ['month', 'Open', 'Close', 'High', 'Low']
                fig = go.Figure(data=[go.Candlestick(x=df_month['month'],
                                                     open=df_month['Open'], high=df_month['High'],
                                                     low=df_month['Low'], close=df_month['Close'])])
                fig.update_layout(xaxis_rangeslider_visible=False, width=1400, height=400,
                                  title_text=f'{tickers_selection[i]} candlestick {candles_selection} chart')
                st.plotly_chart(fig)
            else:
                df_ticker = df_ticker.sort_values(by='Date')
                df_week = df_ticker.groupby(pd.Grouper(key='Date', freq="1W")).agg(
                    {'Open': 'first', 'Close': 'last', 'High': 'max', 'Low': 'min'}).reset_index()
                df_week.columns = ['week', 'Open', 'Close', 'High', 'Low']
                fig = go.Figure(data=[go.Candlestick(x=df_week['week'],
                                                     open=df_week['Open'], high=df_week['High'],
                                                     low=df_week['Low'], close=df_week['Close'])])
                fig.update_layout(xaxis_rangeslider_visible=False, width=1400, height=400,
                                  title_text=f'{tickers_selection[i]} candlestick {candles_selection} chart')
                st.plotly_chart(fig)

        # ================================================
        ## Drop dawm chart
        # ================================================

    # drop_dawn_container = st.container()
    # with drop_dawn_container:
    #     number = st.number_input('Insert a number of days for the window', min_value=10, max_value=1000, value=250,
    #                              step=10)
    #     number = int(number)
            df_drawdown = df.loc[:, df.columns.str.contains('Adj Close') | df.columns.str.contains('Date')].set_index(
            'Date')
            df_drawdown = df_drawdown.reindex(sorted(df.columns), axis=1)
            roll_max = df_drawdown.rolling(center=False, min_periods=1, window=number).max()
            daily_draw_down = df_drawdown / roll_max - 1.0
            max_daily_draw_down = daily_draw_down.rolling(center=False, min_periods=1, window=number).min()
        #for i in range(len(tickers_selection)):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=daily_draw_down.index, y=daily_draw_down.iloc[:, i], name="Daily"))
            fig.add_trace(go.Scatter(x=max_daily_draw_down.index, y=max_daily_draw_down.iloc[:, i],
                                     name="Max"))
            fig.update_layout(barmode='overlay', width=1400, height=400,
                              title=f'{daily_draw_down.columns[i].replace("Adj Close", "")} max drop-down chart ')
            fig.update_traces(opacity=0.75)
            st.plotly_chart(fig)


