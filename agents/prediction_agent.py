# Prediction_agent.py

from uagents import Agent, Context, Bureau
import pandas as pd
import joblib
import os
from common import Message

# Define the path to the model file
MODEL_DIR = os.path.join(os.path.dirname(__file__), "../Machine_Learning_Model")
MODEL_FILE = os.path.join(MODEL_DIR, "Model.pkl")

model = None  # Initialize at module level

# Initialize the PredictionAgent as an instance of Agent
PredictionAgent = Agent(
    name="PredictionAgent",
    seed="prediction_seed",
    endpoint=["http://127.0.0.1:8002"],
)


@PredictionAgent.on_event("startup")
async def load_model(ctx: Context):
    """
    Loads the machine learning model during the agent's startup event.
    """
    global model
    try:
        ctx.logger.info(f"Attempting to load model from {MODEL_FILE}")
        if not os.path.exists(MODEL_FILE):
            ctx.logger.error(f"Model file not found at {MODEL_FILE}.")
            model = None
            return
        model = joblib.load(MODEL_FILE)
        ctx.logger.info("Model loaded successfully.")
    except Exception as e:
        ctx.logger.error(f"Error loading model: {e}")
        model = None
    ctx.logger.info(f"PredictionAgent address: {PredictionAgent.address}")


@PredictionAgent.on_message(model=Message)
async def perform_prediction(ctx: Context, sender: str, msg: Message):
    """
    Receives health data messages, performs predictions, and communicates the results.
    """
    ctx.logger.info(f"Received message from {sender} with data: {msg}")

    if model is None:
        ctx.logger.error("Model is not loaded. Cannot perform prediction.")
        return

    try:
        # Parse blood pressure
        try:
            systolic, diastolic = map(float, msg.blood_pressure.split("/"))
        except ValueError:
            ctx.logger.error(f"Invalid blood_pressure format: {msg.blood_pressure}")
            return

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
        if not isinstance(predictions, list):
            predictions = []
        predictions.append(prediction)
        ctx.storage.set("predictions", predictions)
        ctx.logger.info(f"Stored prediction: {prediction}")
        
        from communication_agent import communication_agent

        communication_agent_address = communication_agent.address

        if communication_agent_address:
            prediction_message = Message(
                heart_rate=msg.heart_rate,
                blood_pressure=msg.blood_pressure,
                temperature=msg.temperature,
                moisture=msg.moisture,
                body_water_content=msg.body_water_content,
                fatigue_level=msg.fatigue_level,
                drowsiness_level=msg.drowsiness_level,
                prediction=prediction,  # Include prediction
            )
            await ctx.send(
                communication_agent_address,
                prediction_message,
            )
            ctx.logger.info(
                f"Sent prediction to CommunicationAgent at {communication_agent_address}: {prediction}"
            )
        else:
            ctx.logger.error("CommunicationAgent address not available.")

    except Exception as e:
        ctx.logger.error(f"Prediction failed: {e}")

from Data_generation_agent import agent

bureau = Bureau()
bureau.add(agent)
bureau.add(PredictionAgent)

if __name__ == "__main__":
    bureau.run()

