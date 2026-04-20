import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest

def train_regression(X, y):
    """Trains a simple Linear Regression model and returns it, along with slope and intercept."""
    if len(X) < 2:
        return None, None, None
    model = LinearRegression().fit(X, y)
    return model, model.coef_[0], model.intercept_

def calculate_severity(deviation, std_dev):
    """Assigns a severity level based on the number of standard deviations."""
    if deviation >= 3 * std_dev:
        return 'Critical'
    elif deviation >= 2 * std_dev:
        return 'Investigate'
    elif deviation > 1.5 * std_dev:
        return 'Warning'
    return 'Normal'

def analyze_point(historical_data, new_time, actual_potency, actual_impurity):
    """
    Main ML analysis function. Combines Linear Regression matching for trend 
    and Isolation Forest for anomaly (OOT) detection.
    """
    report = {
        'is_oot': False,
        'severity': 'Normal',
        'potency_info': {},
        'impurity_info': {},
        'ml_anomaly': False
    }

    n_points = len(historical_data)
    if n_points < 3:
        # Not enough data for statistical deviations or ML, just return baseline
        report['message'] = "Insufficient historical data for accurate ML prediction."
        return report

    df = pd.DataFrame(historical_data)
    X = df[['time_point_month']].values
    y_pot = df['potency'].values
    y_imp = df['impurity'].values

    # 1. Statistical Analysis - Potency
    model_pot, m_pot, c_pot = train_regression(X, y_pot)
    expected_potency = float(model_pot.predict([[new_time]])[0]) if model_pot else None

    # Calculate Standard Deviation of Residuals (with a minimum noise floor so it's not hyper-sensitive)
    residuals_pot = y_pot - model_pot.predict(X)
    std_dev_pot = max(np.std(residuals_pot), 1.0) if len(residuals_pot) > 1 else 1.0  # Min 1.0% tolerance

    dev_pot = abs(actual_potency - expected_potency)
    sev_pot = calculate_severity(dev_pot, std_dev_pot)

    report['potency_info'] = {
        'expected': round(expected_potency, 2),
        'actual': actual_potency,
        'deviation': round(dev_pot, 2),
        'severity': sev_pot
    }

    # 2. Statistical Analysis - Impurity
    model_imp, m_imp, c_imp = train_regression(X, y_imp)
    expected_impurity = float(model_imp.predict([[new_time]])[0]) if model_imp else None

    # Calculate Std Dev (with minimum floor)
    residuals_imp = y_imp - model_imp.predict(X)
    std_dev_imp = max(np.std(residuals_imp), 0.05) if len(residuals_imp) > 1 else 0.1

    dev_imp = abs(actual_impurity - expected_impurity)
    sev_imp = calculate_severity(dev_imp, std_dev_imp)

    report['impurity_info'] = {
        'expected': round(expected_impurity, 2),
        'actual': actual_impurity,
        'deviation': round(dev_imp, 2),
        'severity': sev_imp
    }

    # Determine highest statistical severity
    severities = {'Normal': 0, 'Warning': 1, 'Investigate': 2, 'Critical': 3}
    highest_sev = max(severities[sev_pot], severities[sev_imp])
    rev_severities = {0: 'Normal', 1: 'Warning', 2: 'Investigate', 3: 'Critical'}
    
    report['severity'] = rev_severities[highest_sev]

    # 3. ML Anomaly Detection (Isolation Forest)
    # Using 2D feature space: Potency and Impurity together
    # This evaluates if the combination of points is highly unusual based on patterns.
    X_features = df[['potency', 'impurity']].values
    
    # Needs a minimum number of points to be somewhat meaningful (e.g., 10+)
    # With very few points, IsolationForest forces false positives due to small sample size.
    if n_points >= 10:
        # contamination='auto' prevents forcing anomalies when none exist
        iso = IsolationForest(contamination='auto', random_state=42)
        iso.fit(X_features)
        
        # Predict: 1 is Normal, -1 is Anomaly (OOT)
        anomaly_score = iso.predict([[actual_potency, actual_impurity]])[0]
        
        # IF it's flagged as an anomaly by the forest AND it's moderately deviating statistically 
        # (to prevent pure false positives from the ML boundary on small sets)
        if anomaly_score == -1 and highest_sev >= severities['Warning']:
            report['ml_anomaly'] = True
            report['severity'] = 'Critical'  # Override severity if ML model dictates an anomaly.

    # Final "OOT" boolean trigger
    if report['severity'] in ['Investigate', 'Critical'] or report['ml_anomaly']:
        report['is_oot'] = True

    return report

def predict_shelf_life(historical_data, potency_limit=90.0, impurity_limit=1.0):
    """Predicts shelf life limit intersecting lower bounds."""
    if len(historical_data) < 2:
        return "Insufficient Data"

    df = pd.DataFrame(historical_data)
    X = df[['time_point_month']].values
    y_pot = df['potency'].values
    y_imp = df['impurity'].values

    # Determine Potency Failure Time
    model_pot, _, _ = train_regression(X, y_pot)
    pot_fail_month = float('inf')
    if model_pot and model_pot.coef_[0] < 0:
        pot_fail_month = (potency_limit - model_pot.intercept_) / model_pot.coef_[0]

    # Determine Impurity Failure Time
    model_imp, _, _ = train_regression(X, y_imp)
    imp_fail_month = float('inf')
    if model_imp and model_imp.coef_[0] > 0:
        imp_fail_month = (impurity_limit - model_imp.intercept_) / model_imp.coef_[0]

    fail_month = min(pot_fail_month, imp_fail_month)
    
    last_month = max(df['time_point_month'])
    
    if fail_month > 120:
        return {"shelf_life": ">120m", "remaining": "Stable"}
    if fail_month < last_month:
        return {"shelf_life": f"{int(fail_month)}m", "remaining": "0m"}
        
    return {
        "shelf_life": f"{int(fail_month)}m",
        "remaining": f"{int(fail_month - last_month)}m"
    }
