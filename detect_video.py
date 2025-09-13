import cv2
import torch
import datetime
import numpy as np  
import csv
from sort import Sort  # Make sure you have installed sort: pip install sort

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)

# Open video file
cap = cv2.VideoCapture("traffic.mp4")

# Define codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = None

# Open CSV file for logging
csv_file = open("detections_log.csv", mode="w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["timestamp", "frame_id", "track_id", "class", "confidence", "x1", "y1", "x2", "y2"])

frame_id = 0

# ---------------- NEW: Global cumulative counters ----------------
cumulative_counts = {}
cumulative_total = 0

# ---------------- NEW: SORT Tracker & Counted IDs ----------------
tracker = Sort()
counted_ids = set()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_id += 1
    h, w = frame.shape[:2]

    # ---------------- Detect only in a horizontal strip of the right half ----------------
    y_start = int(h * 0.5)   # lower bound of ROI (adjust as needed)
    y_end = int(h * 0.7)  # This will raise the bottom edge of the box    
    right_half_roi = frame[y_start:y_end, w//2:]

    # Run detection only on ROI
    results = model(right_half_roi)
    df = results.pandas().xyxy[0]

    # Map ROI coordinates back to full frame
    df['xmin'] += w//2
    df['xmax'] += w//2
    df['ymin'] += y_start
    df['ymax'] += y_start

    # Prepare detections for SORT: [x1, y1, x2, y2, score]
    detections = []
    for _, row in df.iterrows():
        # Only consider vehicles (optional: filter by row['name'] if needed)
        detections.append([
            row['xmin'], row['ymin'], row['xmax'], row['ymax'], row['confidence']
        ])
    dets = np.array(detections)

    # Update tracker with detections
    tracked_objects = tracker.update(dets)

    # Draw and count tracked vehicles
    annotated_frame = frame.copy()
    for i, track in enumerate(tracked_objects):
        x1, y1, x2, y2, track_id = track
        # Find the class and confidence for the tracked bbox (nearest match)
        # We use IoU to match detected row to tracked box
        best_match = None
        best_iou = 0
        for _, row in df.iterrows():
            # Calculate IoU
            xx1 = max(x1, row['xmin'])
            yy1 = max(y1, row['ymin'])
            xx2 = min(x2, row['xmax'])
            yy2 = min(y2, row['ymax'])
            w_inter = max(0, xx2 - xx1)
            h_inter = max(0, yy2 - yy1)
            inter = w_inter * h_inter
            area1 = (x2 - x1) * (y2 - y1)
            area2 = (row['xmax'] - row['xmin']) * (row['ymax'] - row['ymin'])
            union = area1 + area2 - inter
            iou = inter / union if union > 0 else 0
            if iou > best_iou:
                best_iou = iou
                best_match = row
        # Only count and log if this track_id has not been counted before
        if int(track_id) not in counted_ids:
            counted_ids.add(int(track_id))
            if best_match is not None:
                label = best_match['name']
                cumulative_counts[label] = cumulative_counts.get(label, 0) + 1
                cumulative_total += 1
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                csv_writer.writerow([
                    timestamp, frame_id, int(track_id), label, round(float(best_match['confidence']), 2),
                    int(x1), int(y1), int(x2), int(y2)
                ])
        # Draw rectangle and label
        box_label = f"ID:{int(track_id)}"
        if best_match is not None:
            box_label += f" {best_match['name']} {best_match['confidence']:.2f}"
        cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(annotated_frame, box_label, (int(x1), int(y1) - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Add overlay text for CUMULATIVE counts
    y = 30
    for label, count in cumulative_counts.items():
        text = f"{label}: {count}"
        cv2.putText(annotated_frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)
        y += 30

    cv2.putText(annotated_frame, f"Total: {cumulative_total}", (10, y + 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    if out is None:
        out = cv2.VideoWriter("output.mp4", fourcc, 20.0, (w, h))

    out.write(annotated_frame)

    cv2.imshow('Annotated Frame', annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
csv_file.close()
cv2.destroyAllWindows()