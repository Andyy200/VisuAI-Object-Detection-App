
import cv2
import argparse
from ultralytics import YOLO
import numpy as np
from g4f.client import Client
import os
from gtts import gTTS
from g4f.errors import RetryProviderError
import sounddevice as sd
import speech_recognition as sr
import io
import time
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YOLOv8 live")
    parser.add_argument(
        "--webcam-resolution",
        default=[1280, 720],
        nargs=2,
        type=int
    )
    parser.add_argument(
        "--horizontal-fov",
        default=70.0,
        type=float,
        help="Horizontal field of view of the webcam in degrees"
    )
    args = parser.parse_args()
    return args

def get_object_color(frame, bbox):
    x1, y1, x2, y2 = bbox
    object_region = frame[int(y1):int(y2), int(x1):int(x2)]
    mean_color = cv2.mean(object_region)[:3]
    return mean_color

def color_to_description(color):
    color = np.array(color)
    if np.all(color < [50, 50, 50]):
        return "very dark"
    elif np.all(color < [100, 100, 100]):
        return "dark"
    elif np.all(color < [150, 150, 150]):
        return "medium"
    elif np.all(color < [200, 200, 200]):
        return "light"
    else:
        return "very light"

def calculate_angle(position, fov, frame_size):
    center = frame_size / 2
    relative_position = position - center
    angle = (relative_position / center) * (fov / 2)
    return angle

def describe_position(center_x, center_y, frame_width, frame_height):
    horizontal_pos = "center"
    vertical_pos = "center"
    if center_x < frame_width / 3:
        horizontal_pos = "left"
    elif center_x > 2 * frame_width / 3:
        horizontal_pos = "right"
    if center_y < frame_height / 3:
        vertical_pos = "top"
    elif center_y > 2 * frame_height / 3:
        vertical_pos = "bottom"
    return f"{vertical_pos} {horizontal_pos}"

def size_description(width, height, frame_width, frame_height):
    object_area = width * height
    frame_area = frame_width * frame_height
    size_ratio = object_area / frame_area
    if size_ratio < 0.05:
        return "small"
    elif size_ratio < 0.2:
        return "medium"
    else:
        return "large"

def draw_boxes(frame, results, model, h_fov, frame_width, frame_height):
    object_descriptions = []
    class_counts = {}

    for result in results:
        if result.boxes.xyxy.shape[0] == 0:
            continue

        for i in range(result.boxes.xyxy.shape[0]):
            bbox = result.boxes.xyxy[i].cpu().numpy()
            confidence = result.boxes.conf[i].cpu().numpy()
            class_id = result.boxes.cls[i].cpu().numpy()
            class_name = model.names[int(class_id)]

            color = (0, 255, 0) if class_name != "mouse" else (255, 0, 0)
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), color, 2)
            label = f"{class_name} {confidence:.2f}"
            cv2.putText(frame, label, (int(bbox[0]), int(bbox[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            mean_color = get_object_color(frame, bbox)
            color_description = color_to_description(mean_color)
            object_width = bbox[2] - bbox[0]
            object_height = bbox[3] - bbox[1]
            size_desc = size_description(object_width, object_height, frame_width, frame_height)
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            h_angle = calculate_angle(center_x, h_fov, frame_width)
            v_angle = calculate_angle(center_y, h_fov * (frame_height / frame_width), frame_height)

            direction = describe_position(center_x, center_y, frame_width, frame_height)
            description = (f"I see a {size_desc} {class_name} at the {direction}. "
                           f"The color of the object is {color_description}. It is positioned at an angle of {h_angle:.2f} degrees horizontally and "
                           f"{v_angle:.2f} degrees vertically.")
            object_descriptions.append(description)

            if class_name in class_counts:
                class_counts[class_name] += 1
            else:
                class_counts[class_name] = 1

    scene_summary = "Here's what I see: " + ", ".join([f"{count} {name}(s)" for name, count in class_counts.items()])
    return object_descriptions, scene_summary

def generate_scene_description(object_descriptions, scene_summary):
    client = Client()
    scene_description_prompt = (f"Based on the detected objects, here is a summary of the scene:\n"
                                f"{scene_summary}\n"
                                f"Detailed descriptions of the objects:\n" + "\n".join(object_descriptions) + "\n"
                                f" You are a helpful assistant that will take the summary of the scene and output a brief but descriptive response. I am a blind person that needs to know the basics of the environment and what the current scene entails. Please describe the scene in a natural, brief, but all encapsulating manner.")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": scene_description_prompt}]
        )
        return response.choices[0].message.content
    except RetryProviderError as e:
        return "I'm currently unable to provide a detailed scene description. Please try again later."

def generate_user_query_response(user_query):
    client = Client()
    query_prompt = (f"The user has asked: {user_query}\n"
                    f"Based on the context of the environment and scene, provide a clear and concise response to the user's query.")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": query_prompt}]
        )
        return response.choices[0].message.content
    except RetryProviderError as e:
        return "I'm currently unable to process your query. Please try again later."

def speak_text(text, speed=1.5):  # speed is a multiplier, 1.0 is normal speed
    try:
        tts = gTTS(text, lang='en')
        audio_path = "output.mp3"
        tts.save(audio_path)
        
        # Check if file is created
        if not os.path.exists(audio_path):
            print("Error: Audio file was not created.")
            return

        # Load the audio file
        audio = AudioSegment.from_mp3(audio_path)
        
        # Adjust the speed
        new_sample_rate = int(audio.frame_rate * speed)
        slowed_audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
        slowed_audio = slowed_audio.set_frame_rate(audio.frame_rate)
        
        # Play the audio
        play(slowed_audio)

    except Exception as e:
        print(f"An error occurred during text-to-speech: {e}")

    except Exception as e:
        print(f"An error occurred during text-to-speech: {e}")

def record_audio(duration=5):
    recognizer = sr.Recognizer()
    audio_data = None

    def callback(indata, frames, time, status):
        nonlocal audio_data
        audio_data = indata.tobytes()

    with sd.InputStream(samplerate=16000, channels=1, callback=callback):
        print("Listening...")
        sd.sleep(duration * 1000)

    if audio_data:
        audio_file = io.BytesIO(audio_data)
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
            try:
                return recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                return "Sorry, I didn't catch that."
            except sr.RequestError:
                return "Sorry, I'm having trouble with the speech recognition service."

    return "No audio detected."

def initialize_camera(frame_width, frame_height):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    return cap

def load_yolo_model():
    return YOLO("yolov8l.pt")

def main():
    args = parse_arguments()
    frame_width, frame_height = args.webcam_resolution
    h_fov = args.horizontal_fov

    cap = initialize_camera(frame_width, frame_height)
    model = load_yolo_model()

    last_update_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, agnostic_nms=True)

        if results:
            object_descriptions, scene_summary = draw_boxes(frame, results, model, h_fov, frame_width, frame_height)

            if time.time() - last_update_time > 8:
                scene_description = generate_scene_description(object_descriptions, scene_summary)
                speak_text(scene_description)
                last_update_time = time.time()

            cv2.imshow("YOLOv8 Detection", frame)

        key = cv2.waitKey(1)
        if key == 27:  # Esc key to exit
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()