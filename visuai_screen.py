import kivy
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import numpy as np
from g4f.client import Client
import threading
import sounddevice as sd
import speech_recognition as sr
import io
from kivy.uix.screenmanager import Screen

try:
    from main import initialize_camera, load_yolo_model, draw_boxes, generate_scene_description, generate_user_query_response, speak_text
except ImportError:
    raise ImportError("Error importing functions from main.py")

class VisuAI(Screen):
    def __init__(self, **kwargs):
        super(VisuAI, self).__init__(**kwargs)
        
        self.frame_width, self.frame_height = 1280, 720
        self.h_fov = 70.0
        self.camera = None
        self.model = None
        self.update_event = None

        # Layout setup
        self.window = GridLayout(cols=1, padding=10, spacing=10)
        
        # Add title label
        self.window.add_widget(Label(
            text="VisuAI",
            font_size=32,
            size_hint=(1, 0.1),
            halign="center",
            valign="middle"
        ))

        # Add video feed
        self.video_feed = Image(size_hint=(1, 0.5))
        self.window.add_widget(self.video_feed)

        # Add buttons
        self.button_desc = Button(
            text="Describe Scene",
            size_hint=(1, 0.1)
        )
        self.button_desc.bind(on_press=self.on_button_click)
        self.window.add_widget(self.button_desc)

        self.button_audio = Button(
            text="Audio Input",
            size_hint=(1, 0.1)
        )
        self.button_audio.bind(on_press=self.on_audio_click)
        self.window.add_widget(self.button_audio)

        self.button_reset = Button(
            text="Reset",
            size_hint=(1, 0.1)
        )
        self.button_reset.bind(on_press=self.on_reset_click)
        self.window.add_widget(self.button_reset)

        # Add scene description label
        self.scene_label = Label(
            text="",
            font_size=20,
            size_hint=(1, 0.1),
            halign="center",
            valign="middle"
        )
        self.window.add_widget(self.scene_label)

        self.add_widget(self.window)

    def on_enter(self, *args):
        # Initialize camera and model when entering the screen
        if not self.camera:
            self.camera = initialize_camera(self.frame_width, self.frame_height)
            self.model = load_yolo_model()
            self.update_event = Clock.schedule_interval(self.update, 1.0 / 30.0)  # 30 FPS

    def on_leave(self, *args):
        # Release camera and stop updating when leaving the screen
        if self.camera:
            self.camera.release()
            self.camera = None
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None

    def update(self, dt):
        ret, frame = self.camera.read()
        if ret:
            results = self.model(frame, agnostic_nms=True)
            if results:
                object_descriptions, scene_summary = draw_boxes(
                    frame, results, self.model, self.h_fov, self.frame_width, self.frame_height
                )

            # Convert image to texture
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.video_feed.texture = texture

    def on_button_click(self, instance):
        # Stop updating the video feed
        if self.update_event:
            self.update_event.cancel()

        # Announce button action
        speak_text("Describing scene")

        # Start the scene description process in a separate thread
        threading.Thread(target=self.describe_scene).start()

    def describe_scene(self):
        ret, frame = self.camera.read()
        if ret:
            results = self.model(frame, agnostic_nms=True)
            if results:
                object_descriptions, scene_summary = draw_boxes(
                    frame, results, self.model, self.h_fov, self.frame_width, self.frame_height
                )
                scene_description = generate_scene_description(object_descriptions, scene_summary)
                # Update UI on the main thread
                self.scene_label.text = scene_description
                speak_text(scene_description)
                print(scene_description)

    def on_audio_click(self, instance):
        # Stop updating the video feed
        if self.update_event:
            self.update_event.cancel()

        # Announce button action
        speak_text("Processing audio input")

        # Start the audio processing in a separate thread
        threading.Thread(target=self.process_audio).start()

    def process_audio(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source)
            print("Listening...")

            try:
                # Listen for audio input
                audio_data = recognizer.listen(source, timeout=10)  # Listen for up to 10 seconds
                
                # Recognize the speech using Google Web Speech API
                user_query = recognizer.recognize_google(audio_data)
                
                # Announce what the user said
                speak_text(f"You said: {user_query}")
                
                # Generate and speak the response
                response = generate_user_query_response(user_query)
                # Update UI on the main thread
                self.scene_label.text = response
                speak_text(response)
                print(response)
                
            except sr.UnknownValueError:
                print("Sorry, I could not understand the audio.")
                speak_text("Sorry, I could not understand the audio.")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                speak_text("Sorry, there was an error with the audio request.")
            except Exception as e:
                print(f"An error occurred during audio processing: {e}")
                speak_text("There was an error processing your audio input.")

    def on_reset_click(self, instance):
        # Restart updating the video feed
        if self.update_event:
            self.update_event.cancel()
        self.update_event = Clock.schedule_interval(self.update, 1.0 / 30.0)  # 30 FPS
        
        # Reset camera and clear description
        self.scene_label.text = ""
        speak_text("Resetting camera and description")
