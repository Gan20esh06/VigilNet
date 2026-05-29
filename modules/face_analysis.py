import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=10,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


def get_head_pose(frame):
    """Returns list of pose dicts, each with bbox of face."""
    rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    poses   = []

    if not results.multi_face_landmarks:
        return poses

    h, w = frame.shape[:2]

    for face_landmarks in results.multi_face_landmarks:

        nose      = face_landmarks.landmark[1]
        left_eye  = face_landmarks.landmark[33]
        right_eye = face_landmarks.landmark[263]
        forehead  = face_landmarks.landmark[10]
        chin      = face_landmarks.landmark[152]

        nose_x  = nose.x
        nose_y  = nose.y
        le_x    = left_eye.x
        re_x    = right_eye.x
        fore_y  = forehead.y
        chin_y  = chin.y

        eye_center_x = (le_x + re_x) / 2.0
        eye_width    = abs(re_x - le_x)

        if eye_width < 0.01:
            continue

        # Yaw — left/right turn
        nose_offset = (nose_x - eye_center_x) / eye_width
        yaw         = nose_offset * 90.0

        # Pitch — up/down tilt
        face_height = abs(chin_y - fore_y)
        if face_height < 0.01:
            continue
        nose_ratio = (nose_y - fore_y) / face_height
        pitch      = (nose_ratio - 0.50) * 120.0

        # Face bounding box in pixels
        all_x   = [lm.x * w for lm in face_landmarks.landmark]
        all_y   = [lm.y * h for lm in face_landmarks.landmark]
        face_x1 = int(max(0, min(all_x) - 20))
        face_y1 = int(max(0, min(all_y) - 20))
        face_x2 = int(min(w, max(all_x) + 20))
        face_y2 = int(min(h, max(all_y) + 20))
        face_cx = (face_x1 + face_x2) // 2
        face_cy = (face_y1 + face_y2) // 2

        # Thresholds
        YAW_THRESHOLD = 38
        PITCH_DOWN    = 30
        PITCH_UP      = 35

        if yaw > YAW_THRESHOLD:
            status = "LOOKING RIGHT"
            color  = (0, 0, 255)
        elif yaw < -YAW_THRESHOLD:
            status = "LOOKING LEFT"
            color  = (0, 0, 255)
        elif pitch > PITCH_DOWN:
            status = "HEAD DOWN"
            color  = (0, 165, 255)
        elif pitch < -PITCH_UP:
            status = "HEAD UP"
            color  = (0, 165, 255)
        else:
            status = "FOCUSED"
            color  = (0, 255, 0)

        poses.append({
            "yaw":     round(yaw, 1),
            "pitch":   round(pitch, 1),
            "status":  status,
            "color":   color,
            "nose_x":  int(nose_x * w),
            "nose_y":  int(nose_y * h),
            "face_cx": face_cx,
            "face_cy": face_cy,
        })

    return poses


def match_pose_to_student(poses, tracked):
    """
    Match each tracked student box to the nearest
    face pose by checking which face centre falls
    inside each student bounding box.
    Returns dict: {display_id: pose or None}
    """
    matched = {}
    for (display_id, x1, y1, x2, y2) in tracked:
        best_pose = None
        best_dist = float('inf')
        for pose in poses:
            cx = pose["face_cx"]
            cy = pose["face_cy"]
            if x1 < cx < x2 and y1 < cy < y2:
                dist = (abs(cx - (x1+x2)//2) +
                        abs(cy - (y1+y2)//2))
                if dist < best_dist:
                    best_dist = dist
                    best_pose = pose
        matched[display_id] = best_pose
    return matched
def get_lip_movement(face_landmarks, threshold=0.02):
    """
    Detects if lips are moving (mouth open).
    Uses distance between upper and lower lip landmarks.
    Returns True if mouth is open/moving.
    """
    # Upper lip top: 13, Lower lip bottom: 14
    # Outer mouth: 61 (left), 291 (right)
    upper_lip = face_landmarks.landmark[13]
    lower_lip = face_landmarks.landmark[14]
    left_mouth = face_landmarks.landmark[61]
    right_mouth = face_landmarks.landmark[291]

    # Vertical mouth opening distance
    mouth_open = abs(upper_lip.y - lower_lip.y)

    # Normalize by mouth width to handle distance from camera
    mouth_width = abs(left_mouth.x - right_mouth.x)
    if mouth_width < 0.001:
        return False

    ratio = mouth_open / mouth_width
    return ratio > threshold   # threshold ~0.02 = slight opening


def get_head_pose_with_lips(frame):
    """
    Extended version of get_head_pose that also
    returns lip movement status per face.
    """
    rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    poses   = []

    if not results.multi_face_landmarks:
        return poses

    h, w = frame.shape[:2]

    for face_landmarks in results.multi_face_landmarks:

        nose      = face_landmarks.landmark[1]
        left_eye  = face_landmarks.landmark[33]
        right_eye = face_landmarks.landmark[263]
        forehead  = face_landmarks.landmark[10]
        chin      = face_landmarks.landmark[152]

        nose_x  = nose.x
        nose_y  = nose.y
        le_x    = left_eye.x
        re_x    = right_eye.x
        fore_y  = forehead.y
        chin_y  = chin.y

        eye_center_x = (le_x + re_x) / 2.0
        eye_width    = abs(re_x - le_x)
        if eye_width < 0.01:
            continue

        yaw = ((nose_x - eye_center_x) / eye_width) * 90.0

        face_height = abs(chin_y - fore_y)
        if face_height < 0.01:
            continue
        pitch = ((nose_y - fore_y) / face_height - 0.50) * 120.0

        # Face bbox
        all_x   = [lm.x * w for lm in face_landmarks.landmark]
        all_y   = [lm.y * h for lm in face_landmarks.landmark]
        face_x1 = int(max(0, min(all_x) - 20))
        face_y1 = int(max(0, min(all_y) - 20))
        face_x2 = int(min(w, max(all_x) + 20))
        face_y2 = int(min(h, max(all_y) + 20))
        face_cx = (face_x1 + face_x2) // 2
        face_cy = (face_y1 + face_y2) // 2

        # Lip movement
        lips_moving = get_lip_movement(face_landmarks)

        YAW_THRESHOLD = 38
        PITCH_DOWN    = 30
        PITCH_UP      = 35

        if yaw > YAW_THRESHOLD:
            status = "LOOKING RIGHT"
            color  = (0, 0, 255)
        elif yaw < -YAW_THRESHOLD:
            status = "LOOKING LEFT"
            color  = (0, 0, 255)
        elif pitch > PITCH_DOWN:
            status = "HEAD DOWN"
            color  = (0, 165, 255)
        elif pitch < -PITCH_UP:
            status = "HEAD UP"
            color  = (0, 165, 255)
        else:
            status = "FOCUSED"
            color  = (0, 255, 0)

        poses.append({
            "yaw":         round(yaw, 1),
            "pitch":       round(pitch, 1),
            "status":      status,
            "color":       color,
            "nose_x":      int(nose_x * w),
            "nose_y":      int(nose_y * h),
            "face_cx":     face_cx,
            "face_cy":     face_cy,
            "lips_moving": lips_moving,
        })

    return poses