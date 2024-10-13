# Prediction_agent.py

from uagents import Agent, Context, Bureau
import pandas as pd
import joblib
import os
from common import Message

# Define the path to the model file
model_file = os.path.join(
    os.path.dirname(__file__), "../Machine_Learning_Model/Model.pkl"
)
model = None  # Initialize at module level

# Initialize the PredictionAgent as an instance of Agent
PredictionAgent = Agent(
    name="PredictionAgent",
    seed="prediction_seed",
    endpoint=["http://127.0.0.1:8001/submit"],  # Ensure this endpoint is correct
)


@PredictionAgent.on_event("startup")
async def load_model(ctx: Context):
    global model
    try:
        if not os.path.exists(model_file):
            ctx._logger.error(f"Model file not found at {model_file}.")
            model = None
            return
        model = joblib.load(model_file)
        ctx._logger.info("Model loaded successfully.")
    except Exception as e:
        ctx._logger.error(f"Error loading model: {e}")
        model = None
    ctx._logger.info(f"PredictionAgent address: {PredictionAgent.address}")


@PredictionAgent.on_message(model=Message)
async def perform_prediction(ctx: Context, sender: str, msg: Message):
    if model is None:
        ctx._logger.error("Model is not loaded. Cannot perform prediction.")
        return

    try:
        # Parse blood pressure
        systolic, diastolic = map(float, msg.blood_pressure.split("/"))

        # Prepare features for prediction
        features = pd.DataFrame(
            [
                {
                    "heart_rate": msg.heart_rate,
                    "systolic": systolic,
                    "diastolic": diastolic,
                    "temperature": msg.temperature,
                    "moisture": msg.moisture,
                    "body_water_content": msg.body_water_content,
                    "fatigue_level": msg.fatigue_level,
                    "drowsiness_level": msg.drowsiness_level,
                }
            ]
        )

        # Make prediction
        prediction = model.predict(features)[0]
        ctx._logger.info(f"Latest Prediction: {prediction}")

        # Store predictions in shared storage for CommunicationAgent
        ctx.storage.set("latest_prediction", prediction)
        predictions = ctx.storage.get("predictions") or []
        predictions.append(prediction)
        ctx.storage.set("predictions", predictions)

    except Exception as e:
        ctx._logger.error(f"Prediction failed: {e}")


# Initialize the Bureau and add agents
# bureau = Bureau()
# # Ensure 'agent' is correctly imported or defined
# from Data_generation_agent import Get_agent  # Adjust the import as necessary
# data_generator_agent = Get_agent()
# bureau.add(data_generator_agent)
# bureau.add(PredictionAgent)

if __name__ == "__main__":
    PredictionAgent.run()
