# Data_generation_agent.py

from uagents import Agent, Context
import numpy as np
from common import Message
import pandas as pd
import random
  # Moved import to the top

# Initialize the Agent
agent = Agent(name="DataGenerator", seed="seed", endpoint=["http://127.0.0.1:8001"])

# Define the filename globally
fileName = "../data.csv"

# Initialize a global DataFrame variable
df = pd.DataFrame()  # Initialize as empty; will be set in initialize_csv

def generate_blood_pressure():
    systolic = np.random.randint(110, 140)
    diastolic = np.random.randint(75, 90)
    return f"{systolic}/{diastolic}"


@agent.on_event("startup")
async def initialize_csv(ctx: Context):
    global df  # Declare df as global to modify it
    try:
        df = pd.read_csv(fileName)
        ctx.logger.info(f"CSV file '{fileName}' loaded successfully.")
    except FileNotFoundError:
        ctx.logger.info(f"CSV file '{fileName}' not found. Creating a new file.")
        df = pd.DataFrame(columns=Message.__fields__.keys())
        df.to_csv(fileName, index=False)
        ctx.logger.info(f"New CSV file '{fileName}' created with the required columns.")

@agent.on_interval(period=10.0)
async def data_gen_transfering(ctx: Context):
    """
    This function generates new health data, updates the CSV, and sends the data to the PredictionAgent.
    """
    global df  # Declare df as global to modify it

    # Ensure the DataFrame does not exceed 100 rows
    if len(df) >= 100:
        df = df.iloc[1:].reset_index(drop=True)
        ctx.logger.info("DataFrame trimmed to maintain 100 rows.")

    # Generate new health data
    heart_rate = np.random.randint(65, 90)
    blood_pressure = generate_blood_pressure()
    temperature = round(np.random.uniform(36.4, 37.5), 1)
    moisture = round(random.uniform(0.4, 0.7), 2)
    body_water_content = np.random.randint(50, 60)
    fatigue_level = np.random.randint(1, 5)
    drowsiness_level = np.random.randint(1, 4)

    # Create a new data entry
    new_data = {
        "heart_rate": heart_rate,
        "blood_pressure": blood_pressure,
        "temperature": temperature,
        "moisture": moisture,
        "body_water_content": body_water_content,
        "fatigue_level": fatigue_level,
        "drowsiness_level": drowsiness_level,
    }

    # Append the new data to the DataFrame
    new_df = pd.DataFrame([new_data])
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_csv(fileName, index=False)
    ctx.logger.info(f"New data appended to '{fileName}'.")
    from Prediction_agent import PredictionAgent
    # Retrieve the recipient address from PredictionAgent
    recipient_address = PredictionAgent.address
    if not recipient_address:
        ctx.logger.error("Recipient address not available.")
        return

    # Create a Message instance
    message = Message(
        heart_rate=heart_rate,
        blood_pressure=blood_pressure,
        temperature=temperature,
        moisture=moisture,
        body_water_content=body_water_content,
        fatigue_level=fatigue_level,
        drowsiness_level=drowsiness_level,
    )

    # Send the message to the PredictionAgent
    try:
        await ctx.send(
            recipient_address,
            message,
        )
        ctx.logger.info(f"Data sent to PredictionAgent at {recipient_address}.")
    except Exception as e:
        ctx.logger.error(f"Failed to send data to PredictionAgent: {e}")

if __name__ == "__main__":
    agent.run()
