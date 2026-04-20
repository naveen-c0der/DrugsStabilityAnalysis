# Predictive Stability & OOT Alerting System

## Overview
A Machine Learning-powered application for pharmaceutical stability analysis. This system predicts shelf-life based on degradation trends and detects Out-of-Trend (OOT) results in real-time.

## features
- **Dashboard**: Visual overview of active studies and alerts.
- **Data Evaluation**: Historical data analysis of Potency and Impurities.
- **Stability Predictions**: ML-based shelf-life forecasting (Linear Regression).
- **OOT Alerts**: Real-time detection of anomalous data points entry.

## Tech Stack
- **Backend**: Python (Flask)
- **ML Engine**: Scikit-Learn, Pandas, NumPy
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism), JavaScript
- **Visualization**: Chart.js

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. Open your browser and navigate to:
   `http://127.0.0.1:5000`

## Modules
1.  **Data Evaluation**: View historical data logs.
2.  **Stability**: Line charts showing degradation trends.
3.  **New Study**: Input new data points to check for OOT.
