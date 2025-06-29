import pandas as pd
from pmdarima import auto_arima
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import plotly.express as px

'''
# Load data
# df = pd.read_csv('CSV FILE HERE', parse_dates=['Date'])
df = df.sort_values(['Date', 'Crop Type', 'Market Location'])
df['DayOfYear'] = df['Date'].dt.dayofyear
df['Month'] = df['Date'].dt.month
'''

def test_model_performance(crop, location, test_days=30):
    try:
        # Filter data
        crop_data = df[(df['Crop Type'] == crop) &
                      (df['Market Location'] == location)]

        if len(crop_data) < 60:
            return None  # Insufficient data

        # Split data
        train = crop_data.iloc[:-test_days]
        test = crop_data.iloc[-test_days:]

        # Feature engineering
        features = ['Supply Quantity (kg)', 'Avg Temperature (°C)',
                   'Total Rainfall (mm)', 'Avg Humidity (%)',
                   'DayOfYear', 'Month']

        # Time-series model
        arima = auto_arima(train['Market Price (Rs/kg)'], seasonal=True, m=7)

        # Gradient Boosting model
        hgbr = HistGradientBoostingRegressor(max_iter=200)
        hgbr.fit(train[features], train['Market Price (Rs/kg)'])

        # Generate predictions
        arima_pred = arima.predict(n_periods=test_days)
        hgbr_pred = hgbr.predict(test[features])
        final_pred = 0.6*arima_pred + 0.4*hgbr_pred

        # Calculate metrics
        actual = test['Market Price (Rs/kg)'].values
        return {
            'MAE': round(mean_absolute_error(actual, final_pred), 2),
            'RMSE': round(mean_squared_error(actual, final_pred, squared=False), 2),
            'MAPE': round(np.mean(np.abs((actual - final_pred)/actual)) * 100, 1)
        }

    except:
        return None

# Test all crop-location combinations
results = []
for crop in df['Crop Type'].unique():
    for location in df['Market Location'].unique():
        metrics = test_model_performance(crop, location)
        if metrics:
            results.append({
                'Crop': crop,
                'Location': location,
                **metrics
            })

# Display performance metrics
results_df = pd.DataFrame(results)
print("Model Performance Metrics:")
print(results_df)

# Visualize predictions for last tested combination
if len(results) > 0:
    last_result = results[-1]
    crop_data = df[(df['Crop Type'] == last_result['Crop']) &
                 (df['Market Location'] == last_result['Location'])].iloc[-30:]

    fig = px.line(crop_data, x='Date', y='Market Price (Rs/kg)',
                  title=f"{last_result['Crop']} Prices in {last_result['Location']}")
    fig.add_scatter(x=crop_data['Date'], y=final_pred, name='Predictions')
    fig.show()
