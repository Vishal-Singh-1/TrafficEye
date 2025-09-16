import React, { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from "recharts";

export default function TrafficGraph({ apiUrl = "http://localhost:3000/api/traffic-data" }) {
  const [trafficData, setTrafficData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch(apiUrl)
      .then((res) => {
        if (!res.ok) throw new Error(`Network error: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        const formatted = data.map(item => ({
          time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          vehicles: item.vehicleCount
        }));
        setTrafficData(formatted);
        setError(null);
      })
      .catch((err) => {
        setError(`Failed to load traffic data: ${err.message}`);
        setTrafficData([]);
      })
      .finally(() => setLoading(false));
  }, [apiUrl]);

  const average =
    trafficData.length > 0
      ? trafficData.reduce((sum, d) => sum + d.vehicles, 0) / trafficData.length
      : 0;

  return (
    <div style={{
      width: "100%",
      height: 350,
      background: "#111827",
      borderRadius: "15px",
      padding: "10px",
      boxShadow: "0 4px 20px rgba(0,0,0,0.5)",
      display: "flex",
      flexDirection: "column",
      justifyContent: "space-between",
    }}>
      {loading ? (
        <div style={{ color: "#facc15", textAlign: "center", marginTop: 100, fontSize: 18 }}>
          Loading traffic graph...
        </div>
      ) : error ? (
        <div style={{ color: "red", textAlign: "center", marginTop: 100, fontSize: 16 }}>
          {error}
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={trafficData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorVehicles" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ffa500" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#ffa500" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2c2f3c" />
            <XAxis dataKey="time" stroke="#ccc" tick={{ fontSize: 12 }} />
            <YAxis stroke="#ccc" tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1f2937",
                borderRadius: "8px",
                border: "1px solid #374151",
                color: "#fff",
                fontSize: "12px",
              }}
            />
            <Area
              type="monotone"
              dataKey="vehicles"
              stroke="#ffa500"
              strokeWidth={3}
              fill="url(#colorVehicles)"
              style={{ filter: "drop-shadow(0px 0px 8px rgba(255,165,0,0.8))" }}
            />
            <ReferenceLine
              y={average}
              label={{
                value: `Avg: ${Math.round(average)}`,
                position: "insideTopRight",
                fill: "#facc15",
                fontSize: 12,
              }}
              stroke="#facc15"
              strokeDasharray="5 5"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
      <div style={{
        textAlign: "center",
        color: "#facc15",
        fontSize: 16,
        marginTop: 5,
      }}>
        🚦 Daily Traffic Flow
      </div>
    </div>
  );
}