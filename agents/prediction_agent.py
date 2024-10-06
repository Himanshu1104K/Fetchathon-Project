# PredictionAgent.py

from uagents import Agent
import pandas as pd
import joblib
import threading
import time


class PredictionAgent(Agent):
    def __init__(self, name, data_file, model_file, interval=300):
        super().__init__(name)
        self.data_file = data_file
        self.model_file = model_file
        self.interval = interval  # seconds
        self.latest_prediction = None
        self.predictions = []  # List to store historical predictions
        self.data_lock = threading.Lock()
        self.predictions_lock = threading.Lock()
        self.load_model()

    def load_model(self):
        try:
            self.model = joblib.load(self.model_file)
            print(f"[{self.name}] Model loaded successfully.")
        except Exception as e:
            print(f"[{self.name}] Error loading model: {e}")
            self.model = None

    def perform_prediction(self):
        with self.data_lock:
            try:
                df = pd.read_csv(self.data_file)
                if not df.empty:
                    latest_row = df.iloc[-1]
                    # Extracting relevant features for prediction with proper column names
                    features = pd.DataFrame(
                        [
                            {
                                "heart_rate": latest_row["heart_rate"],
                                "systolic": float(latest_row["blood_pressure"].split("/")[0]),
                                "diastolic": float(latest_row["blood_pressure"].split("/")[1]),
                                "temperature": latest_row["temperature"],
                                "moisture": latest_row["moisture"],
                                "body_water_content": latest_row["body_water_content"],
                                "fatigue_level": latest_row["fatigue_level"],
                                "drowsiness_level": latest_row["drowsiness_level"],
                            }
                        ]
                    )

                    # Make the prediction
                    prediction = self.model.predict(features)
                    self.latest_prediction = prediction[0]

                    # Store the prediction in the predictions list
                    with self.predictions_lock:
                        self.predictions.append(self.latest_prediction)

                    print(
                        f"[{self.name}] Performed prediction: {self.latest_prediction:.2f}"
                    )
            except Exception as e:
                print(f"[{self.name}] Error during prediction: {e}")

    def run(self):
        while True:
            if self.model is not None:
                self.perform_prediction()
            else:
                print(f"[{self.name}] No model loaded. Skipping prediction.")
            time.sleep(self.interval)

    def get_latest_prediction(self):
        with self.predictions_lock:
            return self.latest_prediction

    def get_predictions(self):
        with self.predictions_lock:
            return list(self.predictions)


if __name__ == "__main__":
    agent = PredictionAgent(
        name="PredictionAgent",
        data_file="../data.csv",
        model_file="../Machine_Learning_Model/Model.pkl",
        interval=10,  # Changed to 10 seconds for demonstration purposes
    )
    agent.run()
