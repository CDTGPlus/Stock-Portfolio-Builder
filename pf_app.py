from flask import Flask, render_template, request, jsonify
import pandas as pd
import yfinance as yf
import cvxpy
import plotly.express as px
import plotly.io as pio
from datetime import datetime
from cvxpy import settings
from functools import reduce
from pypfopt.expected_returns import mean_historical_return
from pypfopt.risk_models import CovarianceShrinkage
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices




app = Flask(__name__)

# ---------------------- Utility Functions ----------------------

# Parse user input, limiting the portfolio length to 25 assets
def stock_parse(x):
    tickers = x.split(',')
    return [s.upper().strip() for s in tickers[:25]]  # Ensure no spaces and limit to 25

# Fetch closing price for stock using Yahoo Finance
def get_stock(ticker, start, end):
    try:
        return yf.download(ticker, start=start, end=end)['Close']
    except ValueError as e:
        return f"Error fetching data for {ticker}: {e}"

# Merge closing prices of multiple stocks into a single DataFrame
def combine_stocks(tickers, start, end):
    data_frames = [get_stock(t, start, end) for t in tickers]
    return reduce(lambda left, right: pd.merge(left, right, on='Date', how='outer'), data_frames).dropna(axis=1)

# Portfolio Optimization Function
def optimize_portfolio(portfolio, funds, risk_tolerance):
    
    try:
   
        mu = mean_historical_return(portfolio)
        print("This is the mean historical return:")
        print(mu)
        # S = CovarianceShrinkage(portfolio).ledoit_wolf()
        S = portfolio.pct_change().dropna().cov()
        print("This is the covariance:")
        print(S)
        ef = EfficientFrontier(mu, S)
       
        print('This is the current ef:',ef)
        # Risk-based allocation
        if risk_tolerance < 30:
            ef.min_volatility()
        elif risk_tolerance > 70:
            ef.max_sharpe()
        else:
            target_volatility = 0.1 + (risk_tolerance - 30) / 40 * (0.25 - 0.1)
            ef.efficient_risk(target_volatility)

        weights = ef.clean_weights()
        performance = ef.portfolio_performance(verbose=False)
        print('Here is the return')
        print(performance[0])
        print('Here is the volatility')
        print(performance[1])
        latest_prices = get_latest_prices(portfolio)
        da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=funds)
        allocation, leftover = da.greedy_portfolio()

        #Portfolio Allocation Pie Chart
        allocation_df = pd.DataFrame(list(allocation.items()), columns=['Stock', 'Shares'])
        pie_fig = px.pie(allocation_df, names='Stock', values='Shares', title="Portfolio Allocation")
        pie_chart_json = pio.to_json(pie_fig)  # Convert to JSON

        # Stock price History Line Chart
        price_fig = px.line(portfolio, x=portfolio.index, y=portfolio.columns, title="Stock Price History")
        price_chart_json = pio.to_json(price_fig)  # Convert to JSON

        return {
            "weights": weights,
            "performance": {
                "annual_return": performance[0],
                "annual_volatility": performance[1],
                "sharpe_ratio": performance[2]
            },
            "allocation": allocation,
            "leftover_funds": leftover,
            "pie_chart": pie_chart_json,  #pie chart JSON,
            "price_chart": price_chart_json  #line chart JSON
        }
    except Exception as e:
        print("Optimization Error:", str(e))
        return {"error": str(e)}
    

# ---------------------- Flask Routes "(/)" ----------------------

# Home Page (Render HTML Form)
@app.route('/')
def home():
    return render_template('index.html')

# API Endpoint to Optimize Portfolio
@app.route('/optimize', methods=['POST'])
def optimize():
    try:
        data = request.get_json()
        stocks = stock_parse(data['stocks'])
        start, end, funds, risk_tolerance = data['start'], data['end'], data['funds'], data['risk_tolerance']

        # Convert string dates to datetime
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")

        # Backend Validation
        if start_date < datetime(1995, 1, 1):
            return jsonify({"error": "Start date cannot be before 1995-01-01."})

        if end_date < start_date:
            return jsonify({"error": "End date cannot be before the start date."})

        portfolio = combine_stocks(stocks, start, end)
        # print(portfolio)
        # has_nan = portfolio.isna().any().any()
        # print(has_nan)
        
        result = optimize_portfolio(portfolio, funds, risk_tolerance)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------------- App Run ----------------------
if __name__ == '__main__':
    app.run(debug=True)
