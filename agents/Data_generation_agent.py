
from uagents import Agent, Context
import numpy as np
import asyncio

from common import Message

def generate_blood_pressure():
    systolic = np.random.randint(110, 140)
    diastolic = np.random.randint(75, 90)
    return f"{systolic}/{diastolic}"

agent = Agent(name="DataGenerator", seed="seed")

def Get_agent():
    return agent

@agent.on_interval(period=10.0)
async def initialize_storage(ctx: Context):
    ctx.storage.set("heart_rate", np.random.randint(65, 90))
    ctx.storage.set("blood_pressure", generate_blood_pressure())
    ctx.storage.set("temperature", np.random.randint(36, 38))  # Adjusted to realistic temperature
    ctx.storage.set("moisture", np.random.randint(0, 100))    # Adjusted range
    ctx.storage.set("body_water_content", np.random.randint(50, 70))  # Adjusted range
    ctx.storage.set("fatigue_level", np.random.randint(0, 100))       # Adjusted range
    ctx.storage.set("drowsiness_level", np.random.randint(0, 100))    # Adjusted range

@agent.on_interval(period=10.0)
async def data_transferring(ctx: Context):
    # Dynamically retrieve the recipient address
    from Prediction_agent import PredictionAgent 
    recipient_address = PredictionAgent.address
    if not recipient_address:
        ctx.logger.error("Recipient address not available.")
        return

    await ctx.send(
        recipient_address,
        Message(
            heart_rate=ctx.storage.get("heart_rate"),
            blood_pressure=ctx.storage.get("blood_pressure"),
            temperature=ctx.storage.get("temperature"),
            moisture=ctx.storage.get("moisture"),
            body_water_content=ctx.storage.get("body_water_content"),
            fatigue_level=ctx.storage.get("fatigue_level"),
            drowsiness_level=ctx.storage.get("drowsiness_level"),
        ),
    )

if __name__ == "__main__":
    agent.run()
