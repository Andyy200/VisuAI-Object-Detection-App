from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
import threading
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import os
import tempfile
# Set background color
Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Dark background for a futuristic look

class ColoredBoxLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(ColoredBoxLayout, self).__init__(**kwargs)
        with self.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Box color
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # Add logo or header image
        layout.add_widget(Image(source='logo.png', size_hint=(1, 0.3)))

        # Box for Welcome message
        welcome_box = ColoredBoxLayout(size_hint=(1, 0.2), padding=10)
        welcome_box.add_widget(Label(text="[b][color=00ffff]Welcome to VisuAI![/color][/b]", font_size=36, markup=True))
        layout.add_widget(welcome_box)

        # Box for Instructions
        instructions_box = ColoredBoxLayout(size_hint=(1, 0.4), padding=10)
        instructions_text = (
            "[b][color=00ffff]Instructions:[/color][/b]\n"
            "[color=ffffff]1. The 'Repeat' button is on the far left.[/color]\n"
            "[color=ffffff]2. The 'Speak' button is on the far right.[/color]\n"
            "[color=ffffff]3. Use the 'Describe Scene' button to get a description of the scene.[/color]\n"
            "[color=ffffff]4. Use the 'Audio Input' button to give voice commands.[/color]\n"
            "[color=ffffff]5. Use the 'Reset' button to restart the video feed.[/color]\n"
            "[color=ffffff]6. Click 'Repeat' to hear the last message again.[/color]\n"
            "[color=ffffff]7. Click 'Speak' to give a voice command.[/color]"
        )
        instructions_box.add_widget(Label(text=instructions_text, font_size=22, markup=True, halign="left", valign="middle"))
        layout.add_widget(instructions_box)

        # Box for Purpose
        purpose_box = ColoredBoxLayout(size_hint=(1, 0.2), padding=10)
        purpose_text = (
            "[b][color=00ffff]Purpose:[/color][/b]\n"
            "[color=ffffff]VisuAI assists visually impaired users by describing scenes and processing audio input.[/color]"
        )
        purpose_box.add_widget(Label(text=purpose_text, font_size=24, markup=True, halign="left", valign="middle"))
        layout.add_widget(purpose_box)

        # Box for Functions
        functions_box = ColoredBoxLayout(size_hint=(1, 0.2), padding=10)
        functions_text = (
            "[b][color=00ffff]Functions:[/color][/b]\n"
            "[color=ffffff]• Object detection and description.[/color]\n"
            "[color=ffffff]• Voice command processing.[/color]\n"
            "[color=ffffff]• Text-to-speech responses.[/color]"
        )
        functions_box.add_widget(Label(text=functions_text, font_size=22, markup=True, halign="left", valign="middle"))
        layout.add_widget(functions_box)

        # Box for Buttons
        button_layout = BoxLayout(size_hint=(1, 0.1), padding=10, spacing=20)
        
        # Button to repeat the last message
        self.repeat_button = Button(text="[b][color=00ffff]Repeat[/color][/b]", markup=True, size_hint=(0.5, 1), background_color=(0.3, 0.5, 0.7, 1), font_size=18)
        self.repeat_button.bind(on_press=self.repeat_message)
        button_layout.add_widget(self.repeat_button)


        # Button to login
        login_button = Button(text="[b][color=00ffff]Login[/color][/b]", markup=True, size_hint=(1, 1), background_color=(0.3, 0.5, 0.7, 1), font_size=18)
        login_button.bind(on_press=self.go_to_login)
        button_layout.add_widget(login_button)

        # Button to start recording
        self.speak_button = Button(text="[b][color=00ffff]Speak[/color][/b]", markup=True, size_hint=(0.5, 1), background_color=(0.3, 0.5, 0.7, 1), font_size=18)
        self.speak_button.bind(on_press=self.start_recording)
        button_layout.add_widget(self.speak_button)


        layout.add_widget(button_layout)

        self.add_widget(layout)

        # Initialize and speak welcome message
        self.last_message = "Welcome to VisuAI! You can say 'instructions' for instructions, 'purpose' for purpose, 'functions' for functions, or 'login' to go to the login screen. The 'Repeat' button is on the far left and the 'Speak' button is on the far right."
        self.speak(self.last_message)

    def speak(self, text):
        # Use gTTS for text-to-speech
        tts = gTTS(text=text, lang='en', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            tts.save(temp_file.name)
            playsound(temp_file.name)
        os.remove(temp_file.name)  # Remove the temporary file after playing

    def go_to_login(self, instance):
        # Stop any ongoing speech before transitioning
        self.stop_speech()
        # Schedule the screen transition on the main thread
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'login'))

    def start_recording(self, instance):
        # Start speech recognition in a new thread
        threading.Thread(target=self.record_speech).start()

    def record_speech(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            try:
                audio = recognizer.listen(source)
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")
                # Process the recognized text
                self.process_speech(text)
            except sr.UnknownValueError:
                print("Sorry, I did not understand that.")
                self.speak("Sorry, I did not understand that.")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                self.speak("Sorry, there was an error with the audio request.")

    def process_speech(self, text):
        if 'instructions' in text.lower():
            response = "Instructions: The 'Repeat' button is on the far left and the 'Speak' button is on the far right. Use the 'Describe Scene' button to get a description of the scene, use the 'Audio Input' button to give voice commands, and use the 'Reset' button to restart the video feed."
        elif 'purpose' in text.lower():
            response = "VisuAI assists visually impaired users by describing scenes and processing audio input."
        elif 'functions' in text.lower():
            response = "Functions include object detection and description, voice command processing, and text-to-speech responses."
        elif 'login' in text.lower():
            self.go_to_login(None)
            return
        else:
            response = "Sorry, I didn't understand the command."
        
        self.last_message = response
        self.speak(response)

    def repeat_message(self, instance):
        # Repeat the last spoken message
        self.speak(self.last_message)
    
    def stop_speech(self):
        # Since gTTS and playsound do not have direct support for stopping playback, we handle this by not playing overlapping audio.
        pass
