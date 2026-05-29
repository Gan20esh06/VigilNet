import cv2
import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort

tracker = DeepSort(
    max_age=90,
    n_init=2,
    nms_max_overlap=1.0,
    max_cosine_distance=0.2,
    nn_budget=100,
    embedder="mobilenet",
    half=True,
    bgr=True
)

face_memory      = {}
id_map           = {}
next_display_id  = [1]

SIMILARITY_THRESHOLD = 0.55


def get_face_embedding(frame, x1, y1, x2, y2):
    h         = y2 - y1
    head_y2   = y1 + int(h * 0.4)
    head_crop = frame[max(0, y1):head_y2, max(0, x1):x2]
    if head_crop.size == 0:
        return None
    try:
        resized   = cv2.resize(head_crop, (64, 64))
        gray      = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        embedding = gray.flatten().astype(np.float32)
        norm      = np.linalg.norm(embedding)
        if norm == 0:
            return None
        return embedding / norm
    except Exception:
        return None


def cosine_similarity(a, b):
    return float(
        np.dot(a, b) /
        (np.linalg.norm(a) * np.linalg.norm(b) + 1e-6)
    )


def find_matching_display_id(embedding):
    if embedding is None or not face_memory:
        return None
    best_score = 0
    best_id    = None
    for disp_id, stored_emb in face_memory.items():
        score = cosine_similarity(embedding, stored_emb)
        if score > best_score:
            best_score = score
            best_id    = disp_id
    return best_id if best_score >= SIMILARITY_THRESHOLD else None


def assign_display_id(raw_id, frame, x1, y1, x2, y2):
    if raw_id in id_map:
        emb = get_face_embedding(frame, x1, y1, x2, y2)
        if emb is not None:
            disp_id = id_map[raw_id]
            if disp_id in face_memory:
                face_memory[disp_id] = (
                    face_memory[disp_id] * 0.8 + emb * 0.2
                )
        return id_map[raw_id]

    emb        = get_face_embedding(frame, x1, y1, x2, y2)
    matched_id = find_matching_display_id(emb)

    if matched_id is not None:
        id_map[raw_id] = matched_id
        print(f"Re-identified: Student {matched_id} "
              f"(raw {raw_id})")
        return matched_id

    new_id              = next_display_id[0]
    next_display_id[0] += 1
    id_map[raw_id]      = new_id
    if emb is not None:
        face_memory[new_id] = emb
    print(f"New student: Student {new_id} (raw {raw_id})")
    return new_id


def get_tracked_students(frame, detections):
    if not detections:
        return []

    ds_input = []
    for det in detections:
        x1, y1, x2, y2 = det[0]
        conf = det[1]
        w = x2 - x1
        h = y2 - y1
        if w < 20 or h < 20:
            continue
        ds_input.append(([x1, y1, w, h], conf, "person"))

    if not ds_input:
        return []

    try:
        tracks = tracker.update_tracks(ds_input, frame=frame)
    except Exception as e:
        print(f"Tracker error: {e}")
        return []

    results = []
    for track in tracks:
        if not track.is_confirmed():
            continue
        if track.time_since_update > 5:
            continue
        raw_id = track.track_id
        try:
            x1, y1, x2, y2 = map(int, track.to_ltrb())
        except Exception:
            continue
        fh, fw = frame.shape[:2]
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(fw, x2)
        y2 = min(fh, y2)
        if x2 - x1 < 20 or y2 - y1 < 20:
            continue
        display_id = assign_display_id(
            raw_id, frame, x1, y1, x2, y2
        )
        results.append((display_id, x1, y1, x2, y2))

    return results


def reset_tracker():
    face_memory.clear()
    id_map.clear()
    next_display_id[0] = 1
    print("Tracker fully reset!")