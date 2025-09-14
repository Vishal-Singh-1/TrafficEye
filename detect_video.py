import cv2
import datetime
import numpy as np  
import csv
from sort import Sort  # pip install sort
from ultralytics import YOLO  # pip install ultralytics

vehicle_classes = ['car', 'motorcycle', 'bus']
model = YOLO('yolov8n.pt')

cap = cv2.VideoCapture("traffic.mp4")
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = None
csv_file = open("detections_log.csv", mode="w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["timestamp", "frame_id", "track_id", "class", "confidence", "x1", "y1", "x2", "y2"])

frame_id = 0
cumulative_counts = {}
cumulative_total = 0
tracker = Sort()
counted_ids = set()
track_last_positions = {}

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_id += 1
    h, w = frame.shape[:2]

    # ROI: bigger horizontal strip of right half
    y_start = int(h * 0.4)
    y_end = int(h * 0.8)
    roi = frame[y_start:y_end, w//2:]
    roi_x_offset = w // 2
    roi_y_offset = y_start

    results = model(roi)[0]
    boxes = results.boxes
    names = results.names

    detections = []
    if boxes is not None and boxes.shape[0] > 0:
        boxes_np = boxes.xyxy.cpu().numpy()
        confs_np = boxes.conf.cpu().numpy()
        clss_np = boxes.cls.cpu().numpy().astype(int)
        for i in range(len(boxes_np)):
            class_id = clss_np[i]
            label = names[class_id]
            conf = confs_np[i]
            if label in vehicle_classes and conf > 0.2:
                xmin = boxes_np[i][0] + roi_x_offset
                ymin = boxes_np[i][1] + roi_y_offset
                xmax = boxes_np[i][2] + roi_x_offset
                ymax = boxes_np[i][3] + roi_y_offset
                detections.append([xmin, ymin, xmax, ymax, conf, label])
    dets = np.array([d[:5] for d in detections])

    # SORT tracker
    if len(dets) == 0:
        tracked_objects = np.empty((0, 5))
    else:
        tracked_objects = tracker.update(dets)

    # Counting line logic (move a bit higher in ROI)
    counting_line_y = int(y_start + (y_end - y_start) * 0.5)
    annotated_frame = frame.copy()
    cv2.line(annotated_frame, (roi_x_offset, counting_line_y), (w, counting_line_y), (0,0,255), 2)

    current_ids = set()
    for track in tracked_objects:
        x1, y1, x2, y2, track_id = track
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        current_ids.add(track_id)
        prev_cy = track_last_positions.get(track_id, None)
        track_last_positions[track_id] = cy

        # IoU match for class assignment
        best_match = None
        best_iou = 0
        for det in detections:
            dx1, dy1, dx2, dy2, dconf, dlabel = det
            # Calculate IoU
            xx1 = max(x1, dx1)
            yy1 = max(y1, dy1)
            xx2 = min(x2, dx2)
            yy2 = min(y2, dy2)
            w_inter = max(0, xx2 - xx1)
            h_inter = max(0, yy2 - yy1)
            inter = w_inter * h_inter
            area1 = (x2 - x1) * (y2 - y1)
            area2 = (dx2 - dx1) * (dy2 - dy1)
            union = area1 + area2 - inter
            iou = inter / union if union > 0 else 0
            if iou > best_iou:
                best_iou = iou
                best_match = det

        # Count only when center crosses the line
        if prev_cy is not None and prev_cy < counting_line_y and cy >= counting_line_y:
            if int(track_id) not in counted_ids:
                counted_ids.add(int(track_id))
                if best_match is not None:
                    label = best_match[5]
                    conf = best_match[4]
                    cumulative_counts[label] = cumulative_counts.get(label, 0) + 1
                    cumulative_total += 1
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    csv_writer.writerow([
                        timestamp, frame_id, int(track_id), label, round(float(conf), 2),
                        int(x1), int(y1), int(x2), int(y2)
                    ])
        # Draw rectangle and label
        box_label = f"ID:{int(track_id)}"
        if best_match is not None:
            box_label += f" {best_match[5]} {best_match[4]:.2f}"
        cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(annotated_frame, box_label, (int(x1), int(y1) - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Clean up track_last_positions (keep only current IDs)
    track_last_positions = {tid: pos for tid, pos in track_last_positions.items() if tid in current_ids}

    # Overlay counts
    y_disp = 30
    for label, count in cumulative_counts.items():
        text = f"{label}: {count}"
        cv2.putText(annotated_frame, text, (10, y_disp), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)
        y_disp += 30

    cv2.putText(annotated_frame, f"Total: {cumulative_total}", (10, y_disp + 10),
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