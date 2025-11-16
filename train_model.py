import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# 1. Load the dataset
# Ensure 'cars_data_cleaned.csv' is in the same folder
df = pd.read_csv('cars_data_cleaned.csv')

# 2. Define Features and Target
# We use numeric features that are available in the user input
features = ['Battery', '0-100', 'Top_Speed', 'Range', 'Efficiency', 'Number_of_seats']
target = 'Estimated_US_Value'  # Using US Value as the target price

X = df[features]
y = df[target]

# 3. Split the data (Optional for final training, but good for validation)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Create a Pipeline (Scaler + Model)
# This ensures input data is scaled exactly like the training data
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', RandomForestRegressor(n_estimators=100, random_state=42))
])

# 5. Train the model
pipeline.fit(X_train, y_train)

# 6. Evaluate (Optional)
score = pipeline.score(X_test, y_test)
print(f"Model R² Score: {score:.3f}")

# 7. Save the trained pipeline
joblib.dump(pipeline, 'model.pkl')
print("✅ Model saved as 'model.pkl'")
