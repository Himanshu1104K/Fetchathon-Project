# common.py
from uagents import Model

class Message(Model):
    heart_rate: int
    blood_pressure: str
    temperature: int
    moisture: int
    body_water_content: int
    fatigue_level: int
    drowsiness_level: int
