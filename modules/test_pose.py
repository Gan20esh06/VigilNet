import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=2,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

cap = cv2.VideoCapture(0)
print("Turn head LEFT and RIGHT — watch yaw values")
print("Press Q to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        for face in results.multi_face_landmarks:
            nose      = face.landmark[1]
            left_eye  = face.landmark[33]
            right_eye = face.landmark[263]
            forehead  = face.landmark[10]
            chin      = face.landmark[152]

            eye_center_x = (left_eye.x + right_eye.x) / 2
            eye_width    = abs(right_eye.x - left_eye.x)
            nose_offset  = (nose.x - eye_center_x) / eye_width
            yaw          = nose_offset * 90.0

            face_height  = abs(chin.y - forehead.y)
            nose_ratio   = (nose.y - forehead.y) / face_height
            pitch        = (nose_ratio - 0.50) * 120.0

            # Show on frame
            cv2.putText(frame,
                        f"YAW: {yaw:.1f}",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.0, (0, 255, 0), 2)
            cv2.putText(frame,
                        f"PITCH: {pitch:.1f}",
                        (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.0, (255, 165, 0), 2)

            # Status
            if yaw > 12:
                status = "LOOKING RIGHT"
                color  = (0, 0, 255)
            elif yaw < -12:
                status = "LOOKING LEFT"
                color  = (0, 0, 255)
            elif pitch > 12:
                status = "HEAD DOWN"
                color  = (0, 165, 255)
            else:
                status = "FOCUSED"
                color  = (0, 255, 0)

            cv2.putText(frame, status,
                        (20, 130),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.2, color, 3)

            print(f"yaw={yaw:+.1f}  pitch={pitch:+.1f}  → {status}")

    cv2.imshow("Pose Debug", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()