
from flask import Flask, render_template, request, jsonify
from old_ml_engine import StabilityModel
import pandas as pd
import math

app = Flask(__name__)

# Initialize model
try:
    model = StabilityModel()
except Exception as e:
    print(f"Model Init Error: {e}")
    model = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/studies', methods=['GET'])
def get_studies():
    try:
        # Force reload because users are modifying CSV externally
        global model
        try:
            model = StabilityModel() # Re-reads CSV
        except Exception:
            pass
            
        # Helper to get unique studies
        studies = model.get_all_studies()
        return jsonify(studies)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data', methods=['GET', 'POST'])
def data():
    try:
        if request.method == 'POST':
            # Add new data point
            req_data = request.json
            
            # Helper for safe float conversion
            def safe_float(val, default=0.0):
                try:
                    if val is None or val == '':
                        return default
                    return float(val)
                except (ValueError, TypeError):
                    return default

            # Extract fields matching CSV schema
            new_row = {
                'Study_ID': req_data.get('study_id', 'ST001'),
                'Product_Name': req_data.get('product_name', 'Tablet_A'),
                'Batch_ID': req_data.get('batch_id', 'B2025_01'),
                'Time_Point_Month': int(req_data.get('time')),
                'Test_Date': req_data.get('test_date', '2025-01-01'),
                'Study_Type': req_data.get('study_type', 'Long-term'),
                'Storage_Temperature': safe_float(req_data.get('temp'), 25.0),
                'Storage_Humidity': safe_float(req_data.get('humidity'), 60.0),
                'Packaging_Type': req_data.get('packaging', 'Blister'),
                'Potency_%': safe_float(req_data.get('potency')),
                'Impurity_%': safe_float(req_data.get('impurities')),
                'Moisture_%': safe_float(req_data.get('moisture')),
                'Dissolution_%': safe_float(req_data.get('dissolution')),
                'Potency_Lower': 95.0,
                'Potency_Upper': 105.0,
                'Impurity_Upper': 1.0
            }
            
            # Process in ML Engine
            result = model.add_data(new_row)
            return jsonify(result)
        
        # Return data for a specific study
        study_id = request.args.get('study_id', 'ST001')
        raw_data = model.get_study_data(study_id)
        
        # Sanitize data: Replace NaN/Infinity
        curr_data = []
        for row in raw_data:
            cleaned_row = {}
            for k, v in row.items():
                if isinstance(v, float):
                    if math.isnan(v) or math.isinf(v):
                        cleaned_row[k] = None
                    else:
                        cleaned_row[k] = v
                else:
                    cleaned_row[k] = v
            curr_data.append(cleaned_row)
            
        return jsonify(curr_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['GET'])
def predict():
    # Return next prediction if available
    study_id = request.args.get('study_id', 'ST001')
    try:
        _, forecast = model.train_and_predict(study_id, 'Potency_%')
        shelf_life = model.predict_shelf_life(study_id)
        
        response = {
                 'next_potency': 'Insufficient Data',
                 'shelf_life': 'N/A'
        }

        if forecast is not None and len(forecast) > 0:
             # Handle potential float conversion issues
             val = float(forecast[0])
             if math.isnan(val):
                 val = 0.0
             response['next_potency'] = round(val, 2)
        
        if isinstance(shelf_life, dict):
             response['shelf_life'] = shelf_life.get('total', 'N/A')
             response['remaining_months'] = shelf_life.get('remaining', 'N/A')
        else:
             response['shelf_life'] = shelf_life
             response['remaining_months'] = 'N/A'
             
        return jsonify(response)
    except Exception as e:
        print(f"Prediction Error: {e}")
        return jsonify({'error': str(e), 'next_potency': 'Error', 'shelf_life': 'Error'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
