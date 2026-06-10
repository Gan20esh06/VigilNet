import cv2
import datetime
import os
from collections import deque
from ultralytics import YOLO
from modules.face_analysis import (get_head_pose_with_lips,
                                   match_pose_to_student)
from modules.tracker import get_tracked_students, reset_tracker
from modules.object_detect import detect_objects, draw_objects
from modules.audio_monitor import (start_audio_monitor,
                                   stop_audio_monitor,
                                   get_audio_alert)
from modules.whatsapp_notifier import initialize_whatsapp, send_alert as send_whatsapp_alert

# ── Directories ──────────────────────────────────────────
for d in ["logs", "recordings", "violations"]:
    os.makedirs(d, exist_ok=True)

# ── Models ───────────────────────────────────────────────
model = YOLO("yolov8s.pt")
cap   = cv2.VideoCapture(0)

# ── Video recorder ───────────────────────────────────────
frame_w  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_h  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
fourcc   = cv2.VideoWriter_fourcc(*'XVID')
recorder = cv2.VideoWriter(
    f"recordings/session_{ts}.avi",
    fourcc, 10.0, (frame_w, frame_h)
)

# ── Violation log ────────────────────────────────────────
log_file = open(f"logs/violations_{ts}.txt", "a")


def write_log(message):
    now = datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    log_file.write(f"[{now}] {message}\n")
    log_file.flush()


# ── WhatsApp Notifier ────────────────────────────────────
# Initialize Twilio WhatsApp integration
whatsapp = initialize_whatsapp()
print(f"WhatsApp Status: {whatsapp.get_status()}")
session_id = ts  # Use session timestamp as ID


# ── State ────────────────────────────────────────────────
student_log        = {}
alert_history      = {}
audio_alert_frames = 0

# Audio cooldown — prevent continuous alerts
# after sound stops
AUDIO_COOLDOWN     = 60   # frames to show after sound stops
audio_cooldown_ctr = 0
last_audio_vol     = 0.0

# Lip movement tracking per student
lip_history = {}          # {display_id: deque of bool}


def is_consistently_suspicious(display_id,
                                current_status,
                                window=5):
    if display_id not in alert_history:
        alert_history[display_id] = deque(maxlen=window)
    alert_history[display_id].append(
        current_status != "FOCUSED"
    )
    return sum(alert_history[display_id]) >= 4


def is_lips_moving(display_id, current_moving,
                   window=8):
    """
    Returns True if lips have been moving for
    majority of recent frames — avoids single-frame flicker.
    """
    if display_id not in lip_history:
        lip_history[display_id] = deque(maxlen=window)
    lip_history[display_id].append(current_moving)
    return sum(lip_history[display_id]) >= 4


def compute_risk(away_count, total_frames,
                 object_alerts, audio_alerts):
    gaze_risk   = min(100,
                      (away_count /
                       max(total_frames, 1)) * 200)
    object_risk = min(100, object_alerts * 20)
    audio_risk  = min(100, audio_alerts  * 15)
    return int(0.4 * gaze_risk +
               0.4 * object_risk +
               0.2 * audio_risk)


def risk_color(score):
    if score >= 70:
        return (0, 0, 255)
    elif score >= 40:
        return (0, 165, 255)
    return (0, 200, 0)


# ── Start audio ──────────────────────────────────────────
audio_ok = start_audio_monitor()

print("=" * 45)
print("  VigilNet — Exam Proctoring System")
print("=" * 45)
print(f"  Mic status   : {'ACTIVE' if audio_ok else 'OFF'}")
print(f"  Smart audio  : Lip + Voice combined")
print("  Press Q      : Quit")
print("  Press R      : Reset student IDs")
print("=" * 45)

# ── Main loop ────────────────────────────────────────────
while True:
    ret, frame = cap.read()
    if not ret:
        break

    h_frame, w_frame = frame.shape[:2]

    # ── 1. Person detection ──────────────────────────────
    results    = model(frame, classes=[0], verbose=False)
    detections = []
    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = float(box.conf[0])
        detections.append(
            ([x1, y1, x2, y2], conf, "person")
        )

    # ── 2. Tracking ──────────────────────────────────────
    tracked = get_tracked_students(frame, detections)

    # ── 3. Head pose + lip movement ──────────────────────
    poses    = get_head_pose_with_lips(frame)
    pose_map = match_pose_to_student(poses, tracked)

    # ── 4. Object detection ──────────────────────────────
    suspicious_objects = detect_objects(frame)

    # ── 5. Smart audio check ─────────────────────────────
    audio_vol = get_audio_alert()

    # Update cooldown
    if audio_vol:
        last_audio_vol     = audio_vol
        audio_cooldown_ctr = AUDIO_COOLDOWN
    elif audio_cooldown_ctr > 0:
        audio_cooldown_ctr -= 1

    audio_active = audio_cooldown_ctr > 0

    # ── 6. Draw base frame ───────────────────────────────
    display = frame.copy()

    # Desk zone line
    desk_y = int(h_frame * 0.60)
    cv2.line(display,
             (0, desk_y), (w_frame, desk_y),
             (50, 50, 255), 1)
    cv2.putText(display, "-- desk zone --",
                (w_frame - 160, desk_y - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45, (50, 50, 255), 1)

    # Draw objects
    display = draw_objects(display, suspicious_objects)

    # Phone under desk
    if any(
        obj["label"] == "cell phone" and
        (obj["bbox"][1] + obj["bbox"][3]) // 2 > desk_y
        for obj in suspicious_objects
    ):
        cv2.putText(display,
                    "WARNING: PHONE UNDER DESK!",
                    (20, desk_y - 12),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75, (0, 0, 255), 2)

    # ── 7. Per-student loop ──────────────────────────────
    alert_messages  = []
    violation_found = False

    for (display_id, x1, y1, x2, y2) in tracked:

        if display_id not in student_log:
            student_log[display_id] = {
                "away_count":    0,
                "total_frames":  0,
                "object_alerts": 0,
                "audio_alerts":  0,
            }

        log = student_log[display_id]
        log["total_frames"] += 1

        # ── Head pose for this student ────────────────
        pose   = pose_map.get(display_id)
        color  = (0, 255, 0)
        status = "FOCUSED"

        if pose is not None:
            status = pose["status"]
            color  = pose["color"]
            if status != "FOCUSED":
                log["away_count"] += 1

            # ── SMART AUDIO: lip + voice ──────────────
            # Only alert for talking if BOTH:
            # 1. Audio volume detected
            # 2. This student's lips are moving
            lips_moving = is_lips_moving(
                display_id,
                pose.get("lips_moving", False)
            )

            if audio_active and lips_moving:
                log["audio_alerts"] += 1
                color  = (130, 0, 130)
                status = "TALKING!"
                write_log(
                    f"TALKING — Student {display_id} "
                    f"lips+audio confirmed "
                    f"vol={last_audio_vol}"
                )

            # Draw lip indicator on face
            lx = pose["nose_x"]
            ly = pose["nose_y"] + 20
            lip_color = (0, 255, 255) if lips_moving \
                else (50, 50, 50)
            cv2.circle(display, (lx, ly),
                       5, lip_color, -1)

        else:
            status = "NO FACE"
            color  = (128, 128, 128)

        # ── Object near student ───────────────────────
        for obj in suspicious_objects:
            ox1, oy1, ox2, oy2 = obj["bbox"]
            cx = (ox1 + ox2) // 2
            cy = (oy1 + oy2) // 2
            if x1 < cx < x2 and y1 < cy < y2:
                log["object_alerts"] += 1
                color  = (0, 0, 255)
                status = f'OBJECT:{obj["label"].upper()}'

        # ── Confirmed alert ───────────────────────────
        confirmed = is_consistently_suspicious(
            display_id, status
        )

        # ── Scores ───────────────────────────────────
        risk = compute_risk(
            log["away_count"],
            log["total_frames"],
            log["object_alerts"],
            log["audio_alerts"]
        )
        rc        = risk_color(risk)
        attention = int(
            100 * (1 - log["away_count"] /
                   max(log["total_frames"], 1))
        )

        # ── Draw student box ──────────────────────────
        box_color = color if confirmed else (0, 200, 0)
        cv2.rectangle(display,
                      (x1, y1), (x2, y2),
                      box_color, 2)

        # Status label
        lbl1 = (f"S{display_id} | {status} | "
                f"Attn:{attention}%")
        cv2.putText(display, lbl1,
                    (x1, max(y1 - 28, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.52, box_color, 2)

        # Risk label
        cv2.putText(display,
                    f"Risk:{risk}%",
                    (x1, max(y1 - 8, 36)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.50, rc, 2)

        # Collect alert
        if confirmed and status not in (
                "FOCUSED", "NO FACE"):
            alert_messages.append(
                f"S{display_id}:{status} "
                f"Risk:{risk}%"
            )
            violation_found = True
            write_log(
                f"VIOLATION — S{display_id} "
                f"| {status} | Risk:{risk}%"
            )
            
            # ── Send WhatsApp alert ──────────────────
            # Extract event type from status
            event_type = status.split(":")[0].strip()
            
            # Prepare event details
            event_details = {
                "event_type": event_type,
                "camera_id": "Camera 1",
                "session_id": session_id,
                "confidence": f"{risk}%",
                "description": (
                    f"Student {display_id} detected: {status}\n"
                    f"Attention Score: {attention}%\n"
                    f"Risk Assessment: {risk}%"
                )
            }
            
            # Send WhatsApp notification with snapshot
            send_whatsapp_alert(
                frame, display_id, status,
                risk, attention,
                event_details
            )

    # ── 8. HUD top left ──────────────────────────────────
    cv2.rectangle(display,
                  (0, 0), (330, 100),
                  (0, 0, 0), -1)
    cv2.rectangle(display,
                  (0, 0), (330, 100),
                  (60, 60, 60), 1)

    cv2.putText(display,
                f"VigilNet  |  Students:{len(tracked)}",
                (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.72, (0, 255, 0), 2)

    # Mic shows actual detection status
    mic_status = "DETECTING" if audio_active else "listening"
    cv2.putText(display,
                (f"Faces:{len(poses)}  "
                 f"Alerts:{len(alert_messages)}  "
                 f"Mic:{mic_status}"),
                (10, 68),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50, (180, 180, 180), 1)

    # ── 9. Smart audio banner ────────────────────────────
    hud_bottom = 100
    if audio_active:
        # Check if any student lips are moving
        any_talking = any(
            is_lips_moving(did, False)
            for (did, _, _, _, _) in tracked
        )
        banner_color = (130, 0, 130) if any_talking \
            else (80, 0, 80)
        banner_text  = (
            "STUDENT TALKING DETECTED!"
            if any_talking
            else "AUDIO: sound detected "
                 "(no lip movement = not student)"
        )
        cv2.rectangle(display,
                      (0, hud_bottom),
                      (w_frame, hud_bottom + 36),
                      banner_color, -1)
        cv2.putText(display, banner_text,
                    (10, hud_bottom + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.62, (255, 255, 255), 2)
        hud_bottom += 36

    # ── 10. Object banner ────────────────────────────────
    if suspicious_objects:
        names = ", ".join(
            o["label"] for o in suspicious_objects
        )
        cv2.rectangle(display,
                      (0, hud_bottom),
                      (w_frame, hud_bottom + 36),
                      (0, 0, 160), -1)
        cv2.putText(display,
                    f"OBJECT: {names.upper()}",
                    (10, hud_bottom + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (255, 255, 255), 2)

    # ── 11. Bottom alert banner ──────────────────────────
    if alert_messages:
        cv2.rectangle(display,
                      (0, h_frame - 48),
                      (w_frame, h_frame),
                      (0, 0, 180), -1)
        text = "ALERT: " + "  |  ".join(alert_messages)
        cv2.putText(display, text,
                    (10, h_frame - 16),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.58, (255, 255, 255), 2)
        print(f"[ALERT] {alert_messages}")
    else:
        cv2.rectangle(display,
                      (0, h_frame - 35),
                      (270, h_frame),
                      (0, 110, 0), -1)
        cv2.putText(display,
                    f"ALL {len(tracked)} STUDENTS FOCUSED",
                    (8, h_frame - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (255, 255, 255), 1)

    # ── 12. Record if violation ──────────────────────────
    if violation_found or audio_active:
        recorder.write(display)

    cv2.imshow("VigilNet — Exam Proctor", display)

    # ── 13. Controls ─────────────────────────────────────
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        reset_tracker()
        student_log.clear()
        alert_history.clear()
        lip_history.clear()
        audio_cooldown_ctr = 0
        print("Full reset!")

# ── Cleanup ──────────────────────────────────────────────
stop_audio_monitor()
cap.release()
recorder.release()
log_file.close()
cv2.destroyAllWindows()
print(f"Session saved → logs/violations_{ts}.txt")