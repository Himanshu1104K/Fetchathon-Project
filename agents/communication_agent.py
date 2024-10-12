# communication_agent.py

from uagents import Agent, Context, Bureau
import asyncio
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import os
import uvicorn  # Ensure uvicorn is installed

# Constants for JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-default-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class CommunicationAgent(Agent):
    def __init__(self, name: str, host: str = "0.0.0.0", port: int = 8000):
        super().__init__(name)
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.setup_routes()

    def setup_routes(self):
        # CORS Middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Adjust as needed for security
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

        # Utility Functions for JWT
        def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=15)
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt

        async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            try:
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
                username: str = payload.get("sub")
                if username is None:
                    raise credentials_exception
                return username
            except JWTError:
                raise credentials_exception

        # Login Endpoint
        @self.app.post("/login")
        async def login(form_data: OAuth2PasswordRequestForm = Depends()):
            username = form_data.username
            password = form_data.password
            # Replace this with your actual authentication logic
            if username != "admin" or password != "password":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": username}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}

        # Data Endpoint
        @self.app.get("/data")
        async def get_data(request: Request, current_user: str = Depends(get_current_user)):
            try:
                storage = request.app.state.agent.ctx.storage
                data = {
                    "heart_rate": storage.get("heart_rate", []),
                    "blood_pressure": storage.get("blood_pressure", []),
                    "temperature": storage.get("temperature", []),
                    "moisture": storage.get("moisture", []),
                    "body_water_content": storage.get("body_water_content", []),
                    "fatigue_level": storage.get("fatigue_level", []),
                    "drowsiness_level": storage.get("drowsiness_level", []),
                }
                return JSONResponse(content=data, status_code=200)
            except Exception as e:
                return JSONResponse(content={"error": str(e)}, status_code=500)

        # Prediction Endpoint
        @self.app.get("/prediction")
        async def get_prediction(request: Request, current_user: str = Depends(get_current_user)):
            try:
                storage = request.app.state.agent.ctx.storage
                latest_prediction = storage.get("latest_prediction")
                if latest_prediction is not None:
                    return {"prediction": latest_prediction}
                else:
                    return {"prediction": "No prediction available yet."}
            except Exception as e:
                return {"error": str(e)}

        # Plot Endpoint
        @self.app.get("/plot")
        async def plot_graph(request: Request, current_user: Optional[str] = Depends(get_current_user)):
            try:
                storage = request.app.state.agent.ctx.storage
                predictions = storage.get("predictions", [])

                if not predictions:
                    raise ValueError("No predictions available.")

                count_variable = list(range(1, len(predictions) + 1))
                normalized_efficiency = [max(0, min(1, pred)) for pred in predictions]

                fig, ax = plt.subplots(figsize=(8, 6))
                ax.plot(count_variable, normalized_efficiency, color="blue", linewidth=2, label="Predicted Efficiency")
                ax.set_ylim(0, 1)
                ax.set_xlabel("Count")
                ax.set_ylabel("Normalized Predicted Efficiency")
                ax.set_title("Count vs Normalized Predicted Efficiency")
                ax.legend()
                plt.tight_layout()

                img = io.BytesIO()
                plt.savefig(img, format="png")
                plt.close(fig)
                img.seek(0)
                return StreamingResponse(img, media_type="image/png")
            except Exception as e:
                return JSONResponse(content={"error": str(e)}, status_code=500)

    async def run_server(self):
        # Assign the agent instance to FastAPI's state for access within routes
        self.app.state.agent = self
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def run(self):
        """Start the Communication Agent's server."""
        await self.run_server()

if __name__ == "__main__":
    # Initialize the Bureau
    bureau = Bureau()

    # Import other agents
    from Data_generation_agent import Get_agent  # Ensure this function returns an instance of DataGeneratorAgent
    from Prediction_agent import PredictionAgent   # Ensure this is correctly imported

    # Initialize agents
    data_generator_agent = Get_agent()
    bureau.add(data_generator_agent)
    bureau.add(PredictionAgent)

    # Initialize Communication Agent
    communication_agent = CommunicationAgent(name="CommunicationAgent", host="0.0.0.0", port=8000)
    bureau.add(communication_agent)

    # Run the Bureau (which runs all agents)
    bureau.run()
