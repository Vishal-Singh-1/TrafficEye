# TrafficEye

TrafficEye is a traffic monitoring system that detects vehicles in traffic videos using YOLO and provides a real-time dashboard UI.

## Features

- **Vehicle detection and counting** using YOLOv5
- **Separate detection stats** for cars, buses, bikes, and persons
- **React-based frontend** with charts and dashboard
- **Backend** written in Python (OpenCV + PyTorch)
- **Visualization** of traffic analytics

## Requirements

### Backend

- Python 3.8+
- Create and activate a virtual environment (recommended)
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### Frontend

- Node.js (v14+ recommended)
- Install dependencies:
  ```bash
  cd frontend
  npm install
  ```

## Setup

### 1. Start the Backend

```bash
python app.py
```
Or follow your backend start script.

### 2. Start the Frontend

```bash
cd frontend
npm start
```
The dashboard will open at `http://localhost:3000`.
