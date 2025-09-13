import cv2
import torch
import datetime
import csv

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
csv_writer.writerow(["timestamp", "frame_id", "class", "confidence", "x1", "y1", "x2", "y2"])

frame_id = 0

# ---------------- NEW: Global cumulative counters ----------------
cumulative_counts = {}
cumulative_total = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_id += 1
    h, w = frame.shape[:2]

    # ---------------- Detect only in right half ----------------
    right_half = frame[:, w//2:]
    results = model(right_half)

    # Convert results to pandas dataframe
    df = results.pandas().xyxy[0]

    # Adjust x-coordinates (shift back to original frame position)
    df['xmin'] += w//2
    df['xmax'] += w//2

    # Count objects by label (frame-wise)
    counts = df['name'].value_counts().to_dict()

    # Update cumulative counters
    for label, count in counts.items():
        cumulative_counts[label] = cumulative_counts.get(label, 0) + count
    cumulative_total += len(df)

    # Log detections into CSV
    for _, row in df.iterrows():
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        csv_writer.writerow([
            timestamp, frame_id, row['name'], round(float(row['confidence']), 2),
            int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
        ])

    # Draw detections on full frame
    annotated_frame = frame.copy()
    for _, row in df.iterrows():
        cv2.rectangle(annotated_frame,
                      (int(row['xmin']), int(row['ymin'])),
                      (int(row['xmax']), int(row['ymax'])),
                      (0, 255, 0), 2)
        cv2.putText(annotated_frame, f"{row['name']} {row['confidence']:.2f}",
                    (int(row['xmin']), int(row['ymin']) - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Add overlay text for CUMULATIVE counts
    y = 30
    for label, count in cumulative_counts.items():
        text = f"{label}: {count}"
        cv2.putText(annotated_frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)
        y += 30

    # NEW: Add cumulative total overlay
    cv2.putText(annotated_frame, f"Total: {cumulative_total}", (10, y + 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    # Initialize video writer after knowing frame size
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