import pandas as pd
from sklearn.ensemble import RandomForestRegressor
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import mean_squared_error
from sklearn.utils import _joblib as jb

data = pd.read_csv('Trainingdata.csv')

data[['systolic', 'diastolic']] = data['blood_pressure'].str.split('/', expand=True)

x = data[['heart_rate', 'systolic', 'diastolic', 'temperature', 'moisture', 'body_water_content', 'fatigue_level', 'drowsiness_level']]
y = data['efficiency']

model = RandomForestRegressor(n_estimators=100,random_state=42)

model.fit(x,y)

jb.dump(model,'Model.pkl')