from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import sys
import time

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, insert_data, log_oot_alert, get_study_data, get_all_batches, get_oot_alerts
from ml_engine import analyze_point, predict_shelf_life

app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database on startup
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/studies', methods=['GET'])
def get_studies():
    batches = get_all_batches()
    if not batches:
        batches = ["STB-001"]
    return jsonify(batches)

@app.route('/api/data', methods=['GET', 'POST'])
def handle_data():
    if request.method == 'POST':
        data = request.json
        print(f"[*] Received Data via {data.get('source', 'manual')}: {data}")
        
        batch_id = data.get('study_id', 'STB-001')
        time_point = float(data.get('time', 0))
        potency = float(data.get('potency', 0.0))
        impurity = float(data.get('impurities', 0.0))
        source = data.get('source', 'manual')
        
        # 1. Get History BEFORE adding the new point
        history = get_study_data(batch_id)
        
        # 2. Run ML Analysis
        analysis_report = analyze_point(history, time_point, potency, impurity)
        
        # 3. Save New Data Point
        insert_data(batch_id, time_point, potency, impurity, source)
        
        # 4. Handle OOT Logging & Real-time Broadcasting
        if analysis_report.get('is_oot'):
            # Emit Socket.IO Alert
            socketio.emit('oot_alert', {
                'batch_id': batch_id,
                'time': time_point,
                'potency': potency,
                'impurity': impurity,
                'severity': analysis_report.get('severity'),
                'details': analysis_report,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S") if 'time' in sys.modules else "Now"
            })
            
            # Log to DB
            if analysis_report['potency_info']['severity'] in ['Investigate', 'Critical']:
                log_oot_alert(batch_id, 'Potency', 
                              analysis_report['potency_info']['expected'],
                              potency, 
                              analysis_report['potency_info']['deviation'],
                              analysis_report['potency_info']['severity'])
                              
            if analysis_report['impurity_info']['severity'] in ['Investigate', 'Critical']:
                log_oot_alert(batch_id, 'Impurity', 
                              analysis_report['impurity_info']['expected'],
                              impurity, 
                              analysis_report['impurity_info']['deviation'],
                              analysis_report['impurity_info']['severity'])
                              
            if analysis_report.get('ml_anomaly'):
                # General ML Anomaly
                log_oot_alert(batch_id, 'ML_Combined_Anomaly', 
                              0, 0, 0, 'Critical')

        # 5. Broadcast generic chart update event
        # This tells the frontend to fetch latest data and update charts
        socketio.emit('chart_update', {'batch_id': batch_id})
        
        # Calculate predictive info for the NEXT month (time_point + 1)
        next_month = int(time_point) + 1
        expected_pot_next = None
        expected_imp_next = None
        
        # Get history again (now with the newly inserted point) for best prediction
        updated_history = get_study_data(batch_id)
        if len(updated_history) >= 2:
            import pandas as pd
            from ml_engine import train_regression
            df = pd.DataFrame(updated_history)
            X = df[['time_point_month']].values
            y_pot = df['potency'].values
            y_imp = df['impurity'].values
            
            m_pot, _, _ = train_regression(X, y_pot)
            if m_pot: expected_pot_next = round(float(m_pot.predict([[next_month]])[0]), 2)
            
            m_imp, _, _ = train_regression(X, y_imp)
            if m_imp: expected_imp_next = round(float(m_imp.predict([[next_month]])[0]), 2)
            
        # Also return the standard HTTP response for manual entry forms
        return jsonify({
            'status': 'success',
            'is_oot': analysis_report.get('is_oot'),
            'severity': analysis_report.get('severity'),
            'report': analysis_report,
            'next_prediction': {
                'month': next_month,
                'potency': expected_pot_next if expected_pot_next else 'N/A',
                'impurity': expected_imp_next if expected_imp_next else 'N/A'
            }
        })

    # GET Method: Return study data
    study_id = request.args.get('study_id', 'STB-001')
    raw_data = get_study_data(study_id)
    
    # Format for frontend compatibility (Matching old CSV structure)
    formatted_data = []
    for row in raw_data:
        formatted_data.append({
            'Study_ID': study_id,
            'Time_Point_Month': row['time_point_month'],
            'Potency_%': row['potency'],
            'Impurity_%': row['impurity']
        })
        
    return jsonify(formatted_data)

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    study_id = request.args.get('study_id', 'STB-001')
    return jsonify(get_oot_alerts(study_id))

@app.route('/api/predict', methods=['GET'])
def get_prediction():
    study_id = request.args.get('study_id', 'STB-001')
    history = get_study_data(study_id)
    
    # Needs format adjustment for the ML Engine
    formatted_history = []
    for row in history:
        formatted_history.append({
            'time_point_month': row['time_point_month'],
            'potency': row['potency'],
            'impurity': row['impurity']
        })
        
    prediction = predict_shelf_life(formatted_history)
    
    # Format response for frontend
    if isinstance(prediction, dict):
        return jsonify({
            'shelf_life': prediction['shelf_life'],
            'remaining_months': prediction['remaining']
        })
    else:
        return jsonify({
            'shelf_life': 'N/A',
            'remaining_months': 'N/A'
        })

if __name__ == '__main__':
    print("[*] Starting StabilAi Real-Time Server with SocketIO...")
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
