import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import plotly.graph_objects as go

def fetch_stock_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

def prepare_data(data):
    data['Date'] = data.index
    data['Date'] = pd.to_datetime(data['Date'])
    data['Days'] = (data['Date'] - data['Date'].min()).dt.days
    return data

def train_model(data):
    X = data[['Days']]
    y = data['Close']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model, X_test, y_test

def predict_future(model, data, days_to_predict):
    last_date = data['Date'].max()
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days_to_predict)
    future_df = pd.DataFrame({'Date': future_dates})
    future_df['Days'] = (future_df['Date'] - data['Date'].min()).dt.days
    future_predictions = model.predict(future_df[['Days']])
    return future_df, future_predictions

def plot_stock_data(data, future_df, future_predictions):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], name='Historical Data'))
    fig.add_trace(go.Scatter(x=future_df['Date'], y=future_predictions, name='Predictions'))
    fig.update_layout(title='Stock Price Prediction', xaxis_title='Date', yaxis_title='Price')
    return fig

def main():
    st.title('Stock Price Prediction App')
    
    ticker = st.text_input('Enter stock ticker (e.g., AAPL, GOOGL):', 'AAPL')
    start_date = st.date_input('Start date', pd.to_datetime('2020-01-01'))
    end_date = st.date_input('End date', pd.to_datetime('today'))
    days_to_predict = st.number_input('Number of days to predict', min_value=1, max_value=365, value=30)

    if st.button('Predict'):
        data = fetch_stock_data(ticker, start_date, end_date)
        if data.empty:
            st.error('No data available for the selected stock and date range.')
            return

        data = prepare_data(data)
        model, X_test, y_test = train_model(data)
        future_df, future_predictions = predict_future(model, data, days_to_predict)

        st.subheader('Stock Price Prediction')
        fig = plot_stock_data(data, future_df, future_predictions)
        st.plotly_chart(fig)

        st.subheader('Model Performance')
        train_score = model.score(data[['Days']], data['Close'])
        test_score = model.score(X_test, y_test)
        st.write(f'Training R-squared: {train_score:.4f}')
        st.write(f'Testing R-squared: {test_score:.4f}')

if __name__ == '__main__':
    main()