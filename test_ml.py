import pandas as pd
from old_ml_engine import StabilityModel
model = StabilityModel()
df = model._get_study_data('ST-001')
print("ST-001 Data:")
print(df[['Time_Point_Month', 'Potency_%']])
print("Shelf Life:", model.predict_shelf_life('ST-001'))
print("Next Prediction:", model.train_and_predict('ST-001'))
