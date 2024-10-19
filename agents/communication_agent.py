from uagents import Agent, Context, Bureau
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt
import io
import os
import uvicorn
import asyncio

# JWT Constants
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-default-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI app setup
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
global shared_storage
global predictions
# Shared data between agents and HTTP
shared_storage = {
    "health_metrics": {
        "heart_rate": [],
        "blood_pressure": [],
        "temperature": [],
        "moisture": [],
        "body_water_content": [],
        "fatigue_level": [],
        "drowsiness_level": [],
    },
    "latest_prediction": None,
}

predictions = []


# JWT utility functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# FastAPI Endpoints
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password
    if username != "admin" or password != "password":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/data")
async def get_data(request: Request, current_user: str = Depends(get_current_user)):
    return JSONResponse(content=shared_storage["health_metrics"], status_code=200)


@app.get("/prediction")
async def get_prediction(
    request: Request, current_user: str = Depends(get_current_user)
):
    latest_prediction = shared_storage["latest_prediction"]

    if latest_prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction available",
        )

    return {"prediction": latest_prediction}


@app.get("/plot")
async def plot_graph(request: Request, current_user: str = Depends(get_current_user)):
    if not predictions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction data available to generate the plot.",
        )

    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(range(1, len(predictions) + 1), predictions, color="blue")
        ax.set_xlabel("Time")
        ax.set_ylabel("Efficiency")
        ax.set_title("Efficiency over Time")
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format="png")
        plt.close(fig)
        img.seek(0)
        return StreamingResponse(img, media_type="image/png")
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# Importing necessary components for agents
from common import Message
from Data_generation_agent import agent
from Prediction_agent import PredictionAgent

communication_agent = Agent(name="communication_agent")

bureau = Bureau()
bureau.add(communication_agent)  # Add CommunicationAgent first
bureau.add(agent)  # Add DataGenerator
bureau.add(PredictionAgent)  # Add PredictionAgent


@communication_agent.on_message(model=Message)
async def receive_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg}")

    # Update health metrics
    metrics = msg.dict()
    for key in shared_storage["health_metrics"].keys():
        if key in metrics and metrics[key] is not None:
            shared_storage["health_metrics"][key].append(metrics[key])
            ctx.logger.info(f"Updated {key}: {shared_storage['health_metrics'][key]}")

    # Update prediction
    if "prediction" in metrics and metrics["prediction"] is not None:
        shared_storage["latest_prediction"] = metrics["prediction"]
        predictions.append(metrics["prediction"])
        ctx.logger.info(f"Received Prediction from {sender}: {metrics['prediction']}")
    else:
        ctx.logger.info(f"No prediction in message from {sender}.")


# Running FastAPI and the Communication Agent
async def start_fastapi():
    config = uvicorn.Config(app, host="0.0.0.0", port=9000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def run_agents():
    await bureau.run()


# Main entry point
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(start_fastapi()),
        loop.create_task(run_agents()),
    ]
    loop.run_until_complete(asyncio.wait(tasks))
