from uagents import Agent, Context, Bureau
from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import pandas as pd
import threading
import os
import matplotlib
import io

matplotlib.use("Agg")  # Use Agg backend for rendering to file
import matplotlib.pyplot as plt


class CommunicationAgent(Agent):
    def __init__(self, name, data_file, prediction_agent, host="0.0.0.0", port=5000):
        super().__init__(name)
        self.data_file = data_file
        self.prediction_agent = prediction_agent  # Reference to PredictionAgent
        self.host = host
        self.port = port
        self.app = Flask(name)
        self.app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "fallback-default-key")
        self.jwt = JWTManager(self.app)
        CORS(self.app)  # Enable CORS for all routes
        self.setup_routes()

    def setup_routes(self):
        @self.app.route("/login", methods=["POST"])
        def login():
            username = request.json.get("username")
            password = request.json.get("password")
            # Implement user verification logic
            if username != "admin" or password != "password":
                return jsonify({"msg": "Bad username or password"}), 401
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200

        @self.app.route("/data", methods=["GET"])
        @jwt_required()
        def get_data():
            """Fetch and return data from the CSV file."""
            try:
                df = pd.read_csv(self.data_file)
                data = df.to_dict(orient="records")
                return jsonify(data), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/prediction", methods=["GET"])
        @jwt_required()
        def get_prediction():
            """Fetch the latest prediction from the PredictionAgent."""
            latest_pred = self.prediction_agent.get_latest_prediction()
            if latest_pred is not None:
                return jsonify({"prediction": latest_pred}), 200
            else:
                return jsonify({"prediction": "No prediction available yet."}), 200

        @self.app.route("/plot", methods=["GET"])
        @jwt_required(optional=True)  # Optional authentication for plot
        def plot_graph():
            """Generate and return a plot of predicted efficiencies."""
            try:
                df = pd.read_csv(self.data_file)
                predictions = self.prediction_agent.get_predictions()

                if len(df) == 0 or len(predictions) == 0:
                    return jsonify({"error": "No data or predictions available."}), 500

                min_length = min(len(df), len(predictions))
                count_variable = df.index[:min_length]
                predicted_efficiency = predictions[:min_length]

                normalized_efficiency = [max(0, min(1, pred)) for pred in predicted_efficiency]

                # Create line plot
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
                return send_file(img, mimetype="image/png")
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def run(self):
        """Run the Flask application."""
        self.app.run(host=self.host, port=self.port)

    async def on_message(self, ctx: Context, sender: str, msg: dict):
        """Handle incoming messages from other agents."""
        # Example message handling, can be customized
        if msg.get("action") == "request_data":
            data_response = await self.get_data()
            await self.send(sender, data_response)

        elif msg.get("action") == "request_prediction":
            prediction_response = await self.get_prediction()
            await self.send(sender, prediction_response)

        elif msg.get("action") == "request_plot":
            plot_response = await self.generate_plot()
            await self.send(sender, plot_response)

    async def generate_plot(self):
        """Generate a plot and return it."""
        try:
            df = pd.read_csv(self.data_file)
            predictions = self.prediction_agent.get_predictions()

            if len(df) == 0 or len(predictions) == 0:
                return {"error": "No data or predictions available."}

            min_length = min(len(df), len(predictions))
            count_variable = df.index[:min_length]
            predicted_efficiency = predictions[:min_length]
            normalized_efficiency = [max(0, min(1, pred)) for pred in predicted_efficiency]

            # Create line plot
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
            return send_file(img, mimetype="image/png")
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    from Prediction_agent import PredictionAgent

    prediction_agent = PredictionAgent(name="PredictionAgent", seed="prediction_seed", endpoint=["http://127.0.0.1:8001/submit"])
    communication_agent = CommunicationAgent(
        name="CommunicationAgent",
        data_file="../data.csv",
        prediction_agent=prediction_agent,
        host="0.0.0.0",
        port=5000
    )

    # Run agents in separate threads
    t1 = threading.Thread(target=prediction_agent.run, daemon=True)
    t2 = threading.Thread(target=communication_agent.run, daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
