# CommunicationAgent.py

from uagents import Agent
from flask import Flask, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import pandas as pd
import threading
import os
import matplotlib

matplotlib.use("Agg")  # Use Agg backend for rendering to file
import matplotlib.pyplot as plt
import io


class CommunicationAgent(Agent):
    def __init__(
        self,
        name,
        data_file,
        prediction_agent,
        host="0.0.0.0",
        port=5000,
        jwt_secret=os.getenv("JWT_SECRET_KEY", "fallback-default-key"),
    ):
        super().__init__(name)
        self.data_file = data_file
        self.prediction_agent = prediction_agent  # Reference to PredictionAgent
        self.host = host
        self.port = port
        self.app = Flask(name)
        self.app.config["JWT_SECRET_KEY"] = jwt_secret
        self.jwt = JWTManager(self.app)
        CORS(self.app)  # Configure appropriately for production
        self.data_lock = threading.Lock()
        self.setup_routes()

    def setup_routes(self):
        @self.app.route("/login", methods=["POST"])
        def login():
            from flask import request

            username = request.json.get("username", None)
            password = request.json.get("password", None)
            # Implement your user verification logic here
            if username != "admin" or password != "password":
                return jsonify({"msg": "Bad username or password"}), 401

            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200

        @self.app.route("/data", methods=["GET"])
        @jwt_required()
        def get_data():
            with self.data_lock:
                try:
                    df = pd.read_csv(self.data_file)
                    data = df.to_dict(orient="records")
                    return jsonify(data), 200
                except Exception as e:
                    return jsonify({"error": str(e)}), 500

        @self.app.route("/prediction", methods=["GET"])
        @jwt_required()
        def get_prediction():
            latest_pred = self.prediction_agent.get_latest_prediction()
            if latest_pred is not None:
                return jsonify({"prediction": latest_pred}), 200
            else:
                return jsonify({"prediction": "No prediction available yet."}), 200

        @self.app.route("/plot")
        @jwt_required(optional=True)  # Optional authentication for plot
        def plot_graph():
            try:
                # Acquire data and predictions
                with self.data_lock:
                    df = pd.read_csv(self.data_file)  # Read data file
                predictions = self.prediction_agent.get_predictions()  # Get predictions

                # Ensure there is data to plot
                min_length = min(len(df), len(predictions))
                if min_length == 0:
                    return jsonify({"error": "No data or predictions available."}), 500

                # Use the index of the dataframe as the count variable
                count_variable = df.index[:min_length]  # x-axis: count or index
                predicted_efficiency = predictions[:min_length]  # y-axis: predictions

                # Normalize the predicted efficiency to be between 0 and 1
                normalized_efficiency = [max(0, min(1, pred)) for pred in predicted_efficiency]

                # Create line plot: Count (X) vs Normalized Predicted Efficiency (Y)
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.plot(
                    count_variable,
                    normalized_efficiency,
                    color="blue",
                    linewidth=2,  # Line width for better visibility
                    label="Predicted Efficiency",
                )
                ax.set_ylim(0, 1)  # Set y-axis limits to range from 0 to 1
                ax.set_xlabel("Count")
                ax.set_ylabel("Normalized Predicted Efficiency")
                ax.set_title("Count vs Normalized Predicted Efficiency")
                ax.legend()
                plt.tight_layout()

                # Save plot to BytesIO
                img = io.BytesIO()
                plt.savefig(img, format="png")
                plt.close(fig)
                img.seek(0)
                return send_file(img, mimetype="image/png")
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def run(self):
        self.app.run(host=self.host, port=self.port)


if __name__ == "__main__":
    from prediction_agent import PredictionAgent

    prediction_agent = PredictionAgent(
        name="PredictionAgent",
        data_file="../data.csv",
        model_file="../Machine_Learning_Model/Model.pkl",
        interval=10,  # Changed to 10 seconds for demonstration purposes
    )
    communication_agent = CommunicationAgent(
        name="CommunicationAgent",
        data_file="../data.csv",
        prediction_agent=prediction_agent,
        host="0.0.0.0",
        port=5000,
        jwt_secret=os.getenv("JWT_SECRET_KEY", "fallback-default-key"),
    )
    # Run agents in separate threads
    import threading

    t1 = threading.Thread(target=prediction_agent.run, daemon=True)
    t2 = threading.Thread(target=communication_agent.run, daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
