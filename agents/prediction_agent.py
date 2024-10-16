# Prediction_agent.py
from uagents import Agent, Context
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
    endpoint=["http://127.0.0.1:8002"],
)


@PredictionAgent.on_event("startup")
async def load_model(ctx: Context):
    global model
    try:
        ctx.logger.info(f"Trying to load model from {model_file}")
        if not os.path.exists(model_file):
            ctx.logger.error(f"Model file not found at {model_file}.")
            model = None
            return
        model = joblib.load(model_file)
        ctx.logger.info("Model loaded successfully.")
    except Exception as e:
        ctx.logger.error(f"Error loading model: {e}")
        model = None
    ctx.logger.info(f"PredictionAgent address: {PredictionAgent.address}")


@PredictionAgent.on_message(model=Message)
async def perform_prediction(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message with data: {msg}")
    if model is None:
        ctx.logger.error("Model is not loaded. Cannot perform prediction.")
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
        ctx.logger.info(f"Latest Prediction: {prediction}")

        # Store predictions in PredictionAgent's storage
        ctx.storage.set("latest_prediction", prediction)
        predictions = ctx.storage.get("predictions") or []
        predictions.append(prediction)
        ctx.storage.set("predictions", predictions)

        # Send prediction to CommunicationAgent
        from communication_agent import communication_agent

        communication_agent_address = communication_agent.address
        if communication_agent:
            await ctx.send(
                communication_agent_address,
                Message(
                    heart_rate=msg.heart_rate,
                    blood_pressure=msg.blood_pressure,
                    temperature=msg.temperature,
                    moisture=msg.moisture,
                    body_water_content=msg.body_water_content,
                    fatigue_level=msg.fatigue_level,
                    drowsiness_level=msg.drowsiness_level,
                    prediction=prediction,  # Include prediction
                ),
            )
            ctx.logger.info(f"Sent prediction to CommunicationAgent: {prediction}")
        else:
            ctx.logger.error("CommunicationAgent not found in Bureau.")

    except Exception as e:
        ctx.logger.error(f"Prediction failed: {e}")

if __name__ == "__main__":
    PredictionAgent.run()