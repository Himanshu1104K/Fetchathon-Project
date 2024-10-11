from uagents import Agent, Context,Bureau
import pandas as pd
import joblib
import os
from common import Message
from Data_generation_agent import agent

model_file = os.path.join(
    os.path.dirname(__file__), "../Machine_Learning_Model/Model.pkl"
)
model = None  # Initialize at module level

PredictionAgent = Agent(
    name="PredictionAgent",
    seed="prediction_seed",
    endpoint=["http://127.0.0.1:8001/submit"],
)


@PredictionAgent.on_event("startup")
async def load_model(ctx: Context):
    global model
    try:
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
    if model is None:
        ctx.logger.error("Model is not loaded. Cannot perform prediction.")
        return

    try:
        systolic, diastolic = map(float, msg.blood_pressure.split("/"))
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
        prediction = model.predict(features)
        ctx.logger.info(f"Latest Prediction: {prediction}")
    except Exception as e:
        ctx.logger.error(f"Prediction failed: {e}")

bureau = Bureau()
bureau.add(agent)
bureau.add(PredictionAgent)
if __name__ == "__main__":
    bureau.run()
