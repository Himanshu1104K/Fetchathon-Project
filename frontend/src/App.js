// App.js

import React, { useEffect, useState } from "react";
import axios from "axios";

function App() {
  const [data, setData] = useState([]);
  const [graphUrl, setGraphUrl] = useState(null);
  const [prediction, setPrediction] = useState("");
  const [error, setError] = useState("");
  const [token, setToken] = useState("");
  const [credentials, setCredentials] = useState({
    username: "",
    password: "",
  });
  const [loadingData, setLoadingData] = useState(false);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [loadingPrediction, setLoadingPrediction] = useState(false);

  // Base URL for API endpoints
  const API_BASE_URL = "http://localhost:8000";

  // Handle user login
  const handleLogin = () => {
    const params = new URLSearchParams();
    params.append("username", credentials.username);
    params.append("password", credentials.password);

    axios
      .post(`${API_BASE_URL}/login`, params, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      })
      .then((response) => {
        setToken(response.data.access_token);
        setError("");
      })
      .catch((err) => {
        setError("Login failed. Please check your credentials.");
        console.error(err);
      });
  };

  // Fetch the graph image from the /plot endpoint
  const fetchGraph = () => {
    if (!token) return; // Ensure token is available

    setLoadingGraph(true);
    const config = {
      headers: { Authorization: `Bearer ${token}` },
      responseType: "blob", // Important for handling binary data
    };

    axios
      .get(`${API_BASE_URL}/plot`, config)
      .then((response) => {
        const imageUrl = URL.createObjectURL(response.data);
        setGraphUrl(imageUrl);
        setLoadingGraph(false);
      })
      .catch((err) => {
        setError("Error fetching graph.");
        console.error(err);
        setLoadingGraph(false);
      });
  };

  // Fetch data and prediction from the respective endpoints
  const fetchData = () => {
    if (!token) return;

    const config = {
      headers: { Authorization: `Bearer ${token}` },
    };

    setLoadingData(true);
    setLoadingPrediction(true);

    // Fetch data
    axios
      .get(`${API_BASE_URL}/data`, config)
      .then((response) => {
        const fetchedData = response.data;

        // Reconstruct the data into an array of objects
        const reconstructedData = fetchedData.heart_rate.map((hr, index) => ({
          heart_rate: hr,
          blood_pressure: fetchedData.blood_pressure[index],
          temperature: fetchedData.temperature[index],
          moisture: fetchedData.moisture[index],
          body_water_content: fetchedData.body_water_content[index],
          fatigue_level: fetchedData.fatigue_level[index],
          drowsiness_level: fetchedData.drowsiness_level[index],
        }));

        setData(reconstructedData);
        setError("");
        setLoadingData(false);
      })
      .catch((err) => {
        setError("Error fetching data.");
        console.error(err);
        setLoadingData(false);
      });

    // Fetch prediction
    axios
      .get(`${API_BASE_URL}/prediction`, config)
      .then((response) => {
        setPrediction(response.data.prediction);
        setLoadingPrediction(false);
      })
      .catch((err) => {
        setPrediction("Error fetching prediction.");
        console.error(err);
        setLoadingPrediction(false);
      });
  };

  // Initialize graph fetching when token changes
  useEffect(() => {
    if (token) {
      fetchGraph();
      const interval = setInterval(fetchGraph, 10000); // Update every 10 seconds
      return () => clearInterval(interval);
    }
  }, [token]);

  // Initialize data fetching when token changes
  useEffect(() => {
    if (token) {
      fetchData(); // Initial fetch
      const interval = setInterval(fetchData, 10000); // Fetch every 10 seconds
      return () => clearInterval(interval); // Cleanup on unmount
    }
  }, [token]);

  // Render the login form if the user is not authenticated
  if (!token) {
    return (
      <div
        className="bg-dark bg-gradient py-5"
        style={{ width: "100vw", height: "100vh" }}
      >
        <div
          className="container text-center my-5 bg-dark text-white d-flex flex-column justify-content-evenly align-items-center App rounded-5 p-5"
          style={{ width: "30%", height: "500px" }}
        >
          <h1 className="p-4" style={{ fontSize: "3rem" }}>
            LOGIN
          </h1>
          {error && <p style={{ color: "red" }}>{error}</p>}
          <input
            className="form-control p-3"
            type="text"
            placeholder="Username"
            value={credentials.username}
            onChange={(e) =>
              setCredentials({ ...credentials, username: e.target.value })
            }
          />
          <br />
          <input
            className="form-control p-3"
            type="password"
            placeholder="Password"
            value={credentials.password}
            onChange={(e) =>
              setCredentials({ ...credentials, password: e.target.value })
            }
          />
          <br />
          <button
            className="btn btn-primary p-2 fs-5"
            style={{ width: "30%" }}
            onClick={handleLogin}
          >
            Login
          </button>
        </div>
      </div>
    );
  }

  // Render the main dashboard after authentication
  return (
    <div className="App bg-dark bg-gradient text-white">
      <div className="row" style={{ height: "100vh" }}>
        {/* Left Column: Health Overview and Graph */}
        <div className="col-7 p-5 text-center">
          <h1>Health Overview</h1>
          <p>{new Date().toLocaleString()}</p>
          {error && <p style={{ color: "red" }}>{error}</p>}
          <div className="px-5">
            {loadingGraph ? (
              <p>Loading graph...</p>
            ) : graphUrl ? (
              <img
                className="p-2"
                src={graphUrl}
                alt="Actual vs Predicted Efficiency"
                style={{
                  maxWidth: "100%",
                  height: "auto",
                  borderRadius: "30px",
                }}
              />
            ) : (
              <p>Graph not available.</p>
            )}
          </div>
        </div>

        {/* Right Column: Prediction and Additional Info */}
        <div
          className="col p-5 text-center bg-black bg-gradient"
          style={{
            borderTopLeftRadius: "50px",
            borderBottomLeftRadius: "50px",
          }}
        >
          {/* Prediction Card */}
          <div className="card text-start" style={{ borderRadius: "25px" }}>
            <div className="card-header fs-3">
              Current Efficiency Status
            </div>
            <div className="card-body">
              <h5 className="card-title">
                Life Efficiency of the Soldier Predicted by Our Model
              </h5>
              {loadingPrediction ? (
                <p>Loading prediction...</p>
              ) : (
                <>
                  <p className="card-text">{`Efficiency : ${(
                    parseFloat(prediction) * 100
                  ).toFixed(2)}%`}</p>
                  <div
                    className="progress"
                    role="progressbar"
                    aria-label="Efficiency Progress"
                    aria-valuenow={`${parseFloat(prediction) * 100}`}
                    aria-valuemin="0"
                    aria-valuemax="100"
                  >
                    <div
                      className="progress-bar"
                      style={{ width: `${parseFloat(prediction) * 100}%` }}
                    ></div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Additional Health Metrics */}
          <div className="row mt-3 px-5">
            <div className="col mt-4">
              {/* Chest Card */}
              <div
                className="card my-4"
                style={{
                  width: "80%",
                  height: "20%",
                  borderRadius: "20px",
                }}
              >
                <div className="card-body">
                  <blockquote className="blockquote mb-0">
                    <p>Chest (in)</p>
                    <footer className="blockquote-footer fs-2">
                      44.5 ↑
                    </footer>
                  </blockquote>
                </div>
              </div>

              {/* Waist Card */}
              <div
                className="card my-4"
                style={{
                  width: "80%",
                  height: "20%",
                  borderRadius: "20px",
                }}
              >
                <div className="card-body">
                  <blockquote className="blockquote mb-0">
                    <p>Waist (in)</p>
                    <footer className="blockquote-footer fs-2">
                      34 ↑
                    </footer>
                  </blockquote>
                </div>
              </div>

              {/* Hip Card */}
              <div
                className="card my-4"
                style={{
                  width: "80%",
                  height: "20%",
                  borderRadius: "20px",
                }}
              >
                <div className="card-body">
                  <blockquote className="blockquote mb-0">
                    <p>Hip (in)</p>
                    <footer className="blockquote-footer fs-2">
                      42.5 ↑
                    </footer>
                  </blockquote>
                </div>
              </div>
            </div>

            {/* Image Section */}
            <div className="col mt-4">
              <img
                src="Group.png"
                alt="Group"
                style={{ height: "75%", borderRadius: "20px" }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;