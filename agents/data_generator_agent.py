# agents/data_generator_agent.py
from uagents import Agent
import pandas as pd
import numpy as np
import time
import threading
import random


def generate_blood_pressure():
    systolic = np.random.randint(110, 140)
    diastolic = np.random.randint(75, 90)
    return f"{systolic}/{diastolic}"


class DataGeneratorAgent(Agent):
    def __init__(self, name, data_file, interval):
        super().__init__(name)
        self.data_file = data_file
        self.interval = interval  # seconds
        self.data_lock = threading.Lock()
        self.initialize_csv()

    def initialize_csv(self):
        with self.data_lock:
            try:
                pd.read_csv(self.data_file)
            except FileNotFoundError:
                df = pd.DataFrame(
                    columns=[
                        "heart_rate",
                        "blood_pressure",
                        "temperature",
                        "moisture",
                        "body_water_content",
                        "fatigue_level",
                        "drowsiness_level",
                    ]
                )  # Replace with your features
                df.to_csv(self.data_file, index=False)

    def generate_random_data(self):
        with self.data_lock:
            df = pd.read_csv(self.data_file)

            # Ensure that only 100 rows are stored in the CSV
            if len(df) >= 100:
                df = df.iloc[1:].reset_index(drop=True)  # Remove the first (oldest) row

            # Generate new data
            heart_rate = np.random.randint(65, 90)
            blood_pressure = generate_blood_pressure()
            temperature = round(np.random.uniform(36.4, 37.5), 1)
            moisture = round(random.uniform(0.4, 0.7), 1)
            body_water_content = np.random.randint(50, 60)
            fatigue_level = np.random.randint(1, 5)
            drowsiness_level = np.random.randint(1, 4)

            new_data = {
                "heart_rate": heart_rate,
                "blood_pressure": blood_pressure,
                "temperature": temperature,
                "moisture": moisture,
                "body_water_content": body_water_content,
                "fatigue_level": fatigue_level,
                "drowsiness_level": drowsiness_level,
            }

            # Append the new data
            new_df = pd.DataFrame([new_data])
            df = pd.concat([df, new_df], ignore_index=True)

            # Save the updated dataframe back to the CSV
            df.to_csv(self.data_file, index=False)

        print(f"[{self.name}] Generated new data: {new_data}")

    def run(self):
        while True:
            self.generate_random_data()
            time.sleep(self.interval)


if __name__ == "__main__":
    agent = DataGeneratorAgent(
        name="DataGenerator", data_file="../data.csv", interval=10
    )
    agent.run()
