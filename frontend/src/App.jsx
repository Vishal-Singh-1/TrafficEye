import React from "react";
import "./index.css"; 
import trafficVideo from "./assets/traffic.mp4";
import TrafficChart from "./TrafficChart.jsx";
const App = () => {
  return (
    <div className="traffic-dashboard">
      <div className="sidebar">
        <h2>TrafficEye</h2>
        <a href="#">Dashboard</a>
        <a href="#">Live Feed</a>
        <a href="#">Reports</a>
        <a href="#">Alerts</a>
        <a href="#">Settings</a>
      </div>

      <div className="main">
        <div className="topbar">
          <span>Welcome, Admin</span>
          <span>🔔 Notifications | 👤 Profile</span>
        </div>

        <div className="content">
          <div className="left-column">
            <div className="live-video">
              <video controls autoPlay muted loop>
                <source src={trafficVideo} type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            </div>

            <div className="small-videos">
              <div className="lane-video">
                <video autoPlay  muted loop>
                 <source src={trafficVideo} type="video/mp4" />
                </video>
                <span>Lane 2 (Stopped)</span>
              </div>
              <div className="lane-video">
                <video autoPlay muted loop>
                 <source src={trafficVideo} type="video/mp4" />
                </video>
                <span>Lane 3 (Stopped)</span>
              </div>
              <div className="lane-video">
                <video autoPlay muted loop>
                  <source src={trafficVideo} type="video/mp4" />
                </video>
                <span>Lane 4 (Stopped)</span>
              </div>
            </div>
          </div>

          <div className="alerts">
        

            <div className="alerts-section">
              <h4>🚦 Vehicles</h4>
              <div className="lane">
                <strong>Lane 1:</strong> `Running | 25 vehicles
              </div>
              <div className="lane">
                <strong>Lane 2:</strong> Stopped | 15 vehicles | Wait: 30 sec
              </div>
              <div className="lane">
                <strong>Lane 3:</strong> Stopped | 40 vehicles | Wait: 70 sec
              </div>
              <div className="lane">
                <strong>Lane 4:</strong> Stopped | 10 vehicles | Wait: 20 sec
              </div>
            </div>

          
      <TrafficChart />
            
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
