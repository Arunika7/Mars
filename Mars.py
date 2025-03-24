import cv2
import numpy as np
import pyttsx3
import speech_recognition as sr
import google.generativeai as genai
import threading
import sys

# === Setup ===
genai.configure(api_key="Add API KEY")
model = genai.GenerativeModel("Add your own model")
engine = pyttsx3.init()
engine.setProperty('rate', 170)

# Constants
width, height = 800, 600
face_color = (20, 20, 20)
eye_border_color = (70, 70, 70)
pupil_color = (255, 255, 0)

# Eye parameters
eye_width, eye_height = 160, 100
eye_y = 220
left_eye_x = 220
right_eye_x = 420

offset_map = {
    "neutral": (0, 0),
    "happy": (10, -5),
    "sad": (-10, 5),
    "angry": (15, 10),
    "talking_open": (0, 0),
    "talking_closed": (0, 0)
}

def draw_eye(frame, x, y, emotion):
    cv2.rectangle(frame, (x, y), (x + eye_width, y + eye_height), eye_border_color, 3)
    pupil_w, pupil_h = 40, 40
    offset_x, offset_y = offset_map.get(emotion, (0, 0))
    pupil_x = x + eye_width // 2 - pupil_w // 2 + offset_x
    pupil_y = y + eye_height // 2 - pupil_h // 2 + offset_y
    cv2.rectangle(frame, (pupil_x, pupil_y), (pupil_x + pupil_w, pupil_y + pupil_h), pupil_color, -1)

def draw_robot_face(emotion):
    frame = np.full((height, width, 3), face_color, dtype=np.uint8)
    cv2.rectangle(frame, (150, 150), (650, 450), (50, 50, 50), 5)
    draw_eye(frame, left_eye_x, eye_y, emotion)
    draw_eye(frame, right_eye_x, eye_y, emotion)

    if emotion == "happy":
        cv2.ellipse(frame, (400, 420), (50, 20), 0, 0, 180, (0, 255, 0), 5)
    elif emotion == "sad":
        cv2.ellipse(frame, (400, 440), (50, 20), 0, 0, -180, (255, 0, 0), 5)
    elif emotion == "angry":
        cv2.line(frame, (340, 430), (460, 430), (0, 0, 255), 4)
    elif emotion == "talking_open":
        cv2.ellipse(frame, (400, 430), (30, 20), 0, 0, 360, (0, 255, 0), -1)
    elif emotion == "talking_closed":
        cv2.line(frame, (370, 430), (430, 430), (0, 255, 0), 4)
    else:
        cv2.line(frame, (360, 430), (440, 430), (180, 180, 180), 2)

    cv2.rectangle(frame, (320, 120), (480, 150), (30, 30, 30), -1)
    cv2.putText(frame, "MARS", (345, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    return frame

def get_voice_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Speak now...")
        try:
            audio = r.listen(source, timeout=5)
            return r.recognize_google(audio)
        except:
            return "Sorry, I couldn't hear you."

def speak(text):
    stop_flag = threading.Event()

    def run_speech():
        engine.say(text)
        engine.runAndWait()
        stop_flag.set()

    speech_thread = threading.Thread(target=run_speech)
    speech_thread.start()

    while not stop_flag.is_set():
        for state in ["talking_open", "talking_closed"]:
            frame = draw_robot_face(state)
            cv2.imshow("Mars Robot Face", frame)
            if cv2.waitKey(100) & 0xFF == 27:
                stop_flag.set()
                engine.stop()
                break

def detect_emotion(text):
    text = text.lower()
    if any(word in text for word in ["happy", "great", "good", "awesome", "love"]):
        return "happy"
    elif any(word in text for word in ["sad", "bad", "upset", "sorry"]):
        return "sad"
    elif any(word in text for word in ["angry", "mad", "furious", "rage"]):
        return "angry"
    else:
        return "neutral"

if __name__ == "__main__":
    # Create OpenCV window and position it to the right side
    cv2.namedWindow("Mars Robot Face", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Mars Robot Face", 800, 600)
    cv2.moveWindow("Mars Robot Face", 1000, 100)  # Adjust based on your screen resolution

    print("Welcome to Mars 🤖")
    mode = input("Choose input mode: (t)ext or (v)oice: ").lower()

    while True:
        try:
            if mode == 'v':
                prompt = get_voice_input()
            else:
                prompt = input("You: ")

            if prompt.lower() in ["exit", "quit", "bye"]:
                print("👋 Exiting Mars...")
                break

            print("🤖 Thinking...")
            response = model.generate_content(prompt).text
            print("Mars:", response)

            emotion = detect_emotion(response)
            speak(response)

            for _ in range(15):
                frame = draw_robot_face(emotion)
                cv2.imshow("Mars Robot Face", frame)
                if cv2.waitKey(100) & 0xFF == 27:
                    break

        except KeyboardInterrupt:
            print("⚠️ Interrupted. Returning to idle.")
            engine.stop()
            continue

    cv2.destroyAllWindows()
