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

  const handleLogin = () => {
    axios
      .post("http://localhost:5000/login", credentials)
      .then((response) => {
        setToken(response.data.access_token);
        setError("");
      })
      .catch((err) => {
        setError("Login failed");
        console.error(err);
      });
  };

  const fetchGraph = () => {
    // Append a timestamp to prevent caching
    setGraphUrl(`http://localhost:5000/plot?${Date.now()}`);
  };

  useEffect(() => {
    fetchGraph();
    const interval = setInterval(fetchGraph,10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = () => {
    if (!token) return;

    const config = {
      headers: { Authorization: `Bearer ${token}` },
    };

    axios
      .get("http://localhost:5000/data", config)
      .then((response) => {
        setData(response.data);
        setError("");
      })
      .catch((err) => {
        setError("Error fetching data");
        console.error(err);
      });

    axios
      .get("http://localhost:5000/prediction", config)
      .then((response) => {
        setPrediction(response.data.prediction);
      })
      .catch((err) => {
        setPrediction("Error fetching prediction");
        console.error(err);
      });
  };

  useEffect(() => {
    fetchData(); // Initial fetch
    const interval = setInterval(fetchData, 10000); // Fetch every 10 seconds
    return () => clearInterval(interval); // Cleanup on unmount
  }, [token]);

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

  return (
    <div className="App bg-dark bg-gradient text-white">
      <div className="row" style={{ height: "100vh" }}>
        <div className="col-7 p-5 text-center">
          <h1>Health Overview</h1>
          <p>{new Date().toString().split(' GMT')[0]}</p>
          {error && <p style={{ color: "red" }}>{error}</p>}
          <div className="px-5" >
            {graphUrl ? (
              <img className="p-2"
                src={graphUrl}
                alt="Actual vs Predicted Efficiency"
                style={{ maxWidth: "100%", height: "auto", borderRadius: "30px" }}
              />
            ) : (
              <p>Loading graph...</p>
            )}
          </div>
        </div>

        <div
          className="col p-5 text-center bg-black bg-gradient"
          style={{
            borderTopLeftRadius: "50px",
            borderBottomLeftRadius: "50px",
          }}
        >
          <div className="card text-start" style={{ borderRadius: "25px" }}>
            <div className="card-header fs-3">
              Current Efficiency Status
            </div>
            <div className="card-body">
              <h5 className="card-title">
                Life Efficiency of the Soldier Predicted by Our Model
              </h5>
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
            </div>
          </div>

          <div className="row mt-3 px-5">
            <div className="col mt-4">
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

            <div className="col mt-4">
              <img src="Group.png" alt="Group" style={{ height: "75%" }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
