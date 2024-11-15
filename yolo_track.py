from ultralytics import YOLO
import cv2
import numpy as np

model = YOLO('yolov5su.pt')
count = 0
cap = cv2.VideoCapture("./Data/Demo5.mp4")

# Define the classes you want to count
count_classes = ['car', 'truck', 'bus', 'bike']

# Dictionary to keep track of counted objects
counted_objects = {}

# Tracking dictionary
tracked_objects = {}

# Counting zone
count_line_y = 600
count_zone_height = 10

# Unique ID counter
next_id = 1

def get_iou(box1, box2):
    # Calculate intersection over union
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Resize frame for faster processing
    frame = cv2.resize(frame, (1280, 720))

    results = model(frame)

    cv2.line(frame, (300, count_line_y), (1500, count_line_y), (0, 255, 0), 2)

    # List to store current frame detections
    current_detections = []

    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        class_id = int(box.cls[0])
        confidence = box.conf[0]
        class_name = results[0].names[class_id]

        if class_name in count_classes:
            current_detections.append((x1, y1, x2, y2, class_name))

    # Match current detections with tracked objects
    for det in current_detections:
        x1, y1, x2, y2, class_name = det
        matched = False
        for obj_id, obj in tracked_objects.items():
            if get_iou(det[:4], obj['box']) > 0.5:  # If IOU > 0.5, consider it the same object
                tracked_objects[obj_id]['box'] = det[:4]
                tracked_objects[obj_id]['last_seen'] = 0
                matched = True
                break
        if not matched:
            # New object detected
            tracked_objects[next_id] = {'box': det[:4], 'class': class_name, 'last_seen': 0}
            next_id += 1

    # Update tracked objects and draw bounding boxes
    objects_to_remove = []
    for obj_id, obj in tracked_objects.items():
        obj['last_seen'] += 1
        if obj['last_seen'] > 10:  # Remove object if not seen for 10 frames
            objects_to_remove.append(obj_id)
            continue

        x1, y1, x2, y2 = obj['box']
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        center_y = int(y1 + (y2 - y1) / 2)
        center_x = int(x1 + (x2 - x1) / 2)

        # Draw center point
        cv2.circle(frame, (center_x, center_y), 2, (0, 0, 255), 1)

        # Check if object is in counting zone and not already counted
        if count_line_y < center_y < count_line_y + count_zone_height:
            if obj_id not in counted_objects:
                count += 1
                counted_objects[obj_id] = True
                cv2.line(frame, (300, count_line_y), (1500, count_line_y), (0, 0, 255), 2)
        
        # Remove object from counted_objects if it's above the counting zone
        elif center_y < count_line_y:
            if obj_id in counted_objects:
                del counted_objects[obj_id]
       
        label = f"{obj['class']} ID:{obj_id}"
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # Remove old objects
    for obj_id in objects_to_remove:
        del tracked_objects[obj_id]

    cv2.putText(frame, f"Count: {count}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    cv2.imshow('Car Tracking & Counting', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()