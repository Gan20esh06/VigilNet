import cv2
from ultralytics import YOLO

object_model = YOLO("yolov8s.pt")

SUSPICIOUS_OBJECTS = {
    67: ("cell phone", (0, 0, 255),   90),
    63: ("laptop",     (0, 0, 255),   80),
    73: ("book",       (0, 165, 255), 50),
}

CONFIDENCE_THRESHOLDS = {
    "cell phone": 0.80,   # was 0.70 — raise higher
    "laptop":     0.80,
    "book":       0.75,
    "default":    0.80,
}

MIN_OBJECT_SIZE = {
    "cell phone": (40,  60),
    "laptop":     (100, 80),
    "book":       (80, 100),
}


def _run_detection(frame, y_offset=0):
    results    = object_model(frame, verbose=False)[0]
    detections = []
    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf   = float(box.conf[0])
        if cls_id not in SUSPICIOUS_OBJECTS:
            continue
        name, color, risk = SUSPICIOUS_OBJECTS[cls_id]
        threshold = CONFIDENCE_THRESHOLDS.get(
            name, CONFIDENCE_THRESHOLDS["default"]
        )
        if conf < threshold:
            continue
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        y1 += y_offset
        y2 += y_offset
        w_box = x2 - x1
        h_box = y2 - y1
        min_w, min_h = MIN_OBJECT_SIZE.get(name, (40, 40))
        if w_box < min_w or h_box < min_h:
            continue
        detections.append({
            "label":      name,
            "confidence": round(conf, 2),
            "bbox":       (x1, y1, x2, y2),
            "color":      color,
            "risk":       risk
        })
    return detections


def _iou(box1, box2):
    x1    = max(box1[0], box2[0])
    y1    = max(box1[1], box2[1])
    x2    = min(box1[2], box2[2])
    y2    = min(box1[3], box2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter == 0:
        return 0
    area1 = (box1[2]-box1[0]) * (box1[3]-box1[1])
    area2 = (box2[2]-box2[0]) * (box2[3]-box2[1])
    return inter / (area1 + area2 - inter)


def _deduplicate(detections, iou_threshold=0.3):
    if not detections:
        return []
    unique = []
    for det in detections:
        is_dup = False
        for i, kept in enumerate(unique):
            if (kept["label"] == det["label"] and
                    _iou(det["bbox"],
                         kept["bbox"]) > iou_threshold):
                if det["confidence"] > kept["confidence"]:
                    unique[i] = det
                is_dup = True
                break
        if not is_dup:
            unique.append(det)
    return unique


def detect_objects(frame):
    all_detections = []
    all_detections += _run_detection(frame)
    h = frame.shape[0]
    bottom = frame[h//2:, :]
    all_detections += _run_detection(bottom, y_offset=h//2)
    return _deduplicate(all_detections)


def draw_objects(frame, detections):
    for obj in detections:
        x1, y1, x2, y2 = obj["bbox"]
        color = obj["color"]
        label = (f'{obj["label"].upper()} '
                 f'{int(obj["confidence"]*100)}% '
                 f'RISK:{obj["risk"]}')
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
        (tw, th), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.rectangle(frame,
                      (x1, y1 - th - 10),
                      (x1 + tw + 6, y1),
                      color, -1)
        cv2.putText(frame, label,
                    (x1 + 3, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (255, 255, 255), 2)
    return frame