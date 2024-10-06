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


def calculate_efficiency(
    heart_rate,
    blood_pressure,
    temperature,
    moisture,
    body_water_content,
    fatigue_level,
    drowsiness_level,
):
    # Normalize parameters
    hr_score = (heart_rate - 65) / (90 - 65)  # Assuming 65-90 normal range
    bp_systolic, bp_diastolic = map(int, blood_pressure.split("/"))
    bp_score = (bp_systolic - 110) / (140 - 110) * 0.5 + (bp_diastolic - 75) / (
        90 - 75
    ) * 0.5  # Systolic & Diastolic
    temp_score = (temperature - 36.4) / (
        37.5 - 36.4
    )  # Assuming normal body temperature range
    moisture_score = (moisture - 0.4) / (0.7 - 0.4)  # Assuming normal moisture range
    bwc_score = (body_water_content - 50) / (60 - 50)  # Assuming normal range
    fatigue_score = 1 - (fatigue_level - 1) / (
        5 - 1
    )  # Assuming fatigue level from 1 to 5
    drowsiness_score = 1 - (drowsiness_level - 1) / (
        4 - 1
    )  # Assuming drowsiness level from 1 to 4

    # Calculate efficiency
    efficiency = (
        0.15 * hr_score
        + 0.15 * bp_score
        + 0.10 * temp_score
        + 0.10 * moisture_score
        + 0.15 * bwc_score
        + 0.20 * fatigue_score
        + 0.15 * drowsiness_score
    )

    return efficiency


class DataGeneratorAgent(Agent):
    def __init__(self, name, data_file, interval=10):
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
                        "efficiency",
                    ]
                )  # Replace with your features
                df.to_csv(self.data_file, index=False)

    def generate_random_data(self):
        with self.data_lock:
            df = pd.read_csv(self.data_file)
            heart_rate = np.random.randint(65, 90)
            blood_pressure = generate_blood_pressure()
            temperature = round(np.random.uniform(36.4, 37.5), 1)
            moisture = round(random.uniform(0.4, 0.7), 1)
            body_water_content = np.random.randint(50, 60)
            fatigue_level = np.random.randint(1, 5)
            drowsiness_level = np.random.randint(1, 4)

            # Calculate efficiency
            efficiency = calculate_efficiency(
                heart_rate,
                blood_pressure,
                temperature,
                moisture,
                body_water_content,
                fatigue_level,
                drowsiness_level,
            )

            new_data = {
                "heart_rate": heart_rate,
                "blood_pressure": blood_pressure,
                "temperature": temperature,
                "moisture": moisture,
                "body_water_content": body_water_content,
                "fatigue_level": fatigue_level,
                "drowsiness_level": drowsiness_level,
                "efficiency": round(efficiency, 2),
            }
            new_df = pd.DataFrame([new_data])
            df = pd.concat([df, new_df], ignore_index=True)
            df.to_csv(self.data_file, index=False)
        print(f"[{self.name}] Generated new data: {new_data}")

    def run(self):
        while True:
            self.generate_random_data()
            time.sleep(self.interval)


if __name__ == "__main__":
    agent = DataGeneratorAgent(
        name="DataGenerator", data_file="Trainingdata.csv", interval=0
    )
    agent.run()
