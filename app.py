import pandas as pd
from hurst import compute_Hc
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN
from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import yfinance as yf
import logging
from logging.handlers import RotatingFileHandler
import nolds
from scipy import stats
import numpy as np

app = Flask(__name__)

handler = RotatingFileHandler('flask.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

def fetch_data(start_date, end_date):
    global df
    print('Downloading SPY data from Yahoo Finance...')
    df = pd.DataFrame()
    ydata = yf.download('SPY', start=start_date, end=end_date)
    df = pd.DataFrame(ydata, columns=['Close'])
    print('Data downloaded.')

start_date = '2022-01-01'
end_date = '2023-12-31'

scheduler = BackgroundScheduler()
scheduler.add_job(fetch_data, 'interval', hours=24, args=(start_date, end_date))
scheduler.start()

fetch_data(start_date, end_date)

@app.route("/")
def visualize():
    global df
    if df is None:
        return "Data not available. Please try again later."

    # Adding 5-period moving average to the dataframe
    df['Moving_Average'] = df['Close'].rolling(window=5).mean()

    # Calculating linear slope
    slope, intercept, r_value, p_value, std_err = stats.linregress(np.arange(len(df['Close'])), df['Close'])

    df['Linear_Slope'] = np.arange(len(df['Close'])) * slope + intercept
    # Calculating Lyapunov exponent
    LE = nolds.lyap_r(df['Close'])

    # Calculating Hurst exponent
    H, c, data = compute_Hc(df['Close'], kind='price', simplified=True)

    p1 = figure(x_axis_type="datetime", title="SPY Time Series", width=800)
    p1.grid.grid_line_alpha=0.3
    p1.xaxis.axis_label = 'Date'
    p1.yaxis.axis_label = 'Price'
    p1.line(df.index, df['Close'], color='#A6CEE3', legend_label='SPY')

    # Creating the statistics string
    stats_string = f"""
    Hurst Exponent: {H}
    Lyapunov Exponent: {LE}
    Mean: {df['Close'].mean()}
    Median: {df['Close'].median()}
    """

    script, div = components(p1)
    cdn_js = CDN.js_files[0]

    return render_template("plot.html", script=script, div=div, cdn_js=cdn_js, stats_string=stats_string)

if __name__ == "__main__":
    app.run(port=8000)