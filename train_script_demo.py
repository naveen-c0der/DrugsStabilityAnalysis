
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# 1. Load Dataset
print("Loading data from stability_data.csv...")
df = pd.read_csv('stability_data.csv')
print(df.head())

# 2. Prepare Feature (X) and Target (y)
X = df[['TimePoint_Months']]
y = df['Potency']

# 3. Initialize and Train Model
model = LinearRegression()
model.fit(X, y)

print("\nModel Trained!")
print(f"Slope (Degradation Rate): {model.coef_[0]:.4f} %/month")
print(f"Intercept (Initial Potency): {model.intercept_:.4f} %")

# 4. Predict Future Validation
future_months = [[12], [24], [36], [48], [60], [72]]
predictions = model.predict(future_months)

print("\nFuture Predictions:")
for m, p in zip(future_months, predictions):
    print(f"Month {m[0]}: {p:.2f}%")

# Optional: Visualization script
# plt.scatter(X, y, color='blue')
# plt.plot(X, model.predict(X), color='red')
# plt.show()
