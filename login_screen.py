from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.image import Image

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)

        # Create the main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Background image or logo
        logo = Image(source='logo.png', size_hint=(1, 0.4))
        layout.add_widget(logo)

        # Username input
        username_box = BoxLayout(orientation='horizontal', padding=10, spacing=10)
        username_box.add_widget(Label(text="Username:", font_size=20, size_hint=(0.3, 1)))
        self.username_input = TextInput(size_hint=(0.7, 1))
        username_box.add_widget(self.username_input)
        layout.add_widget(username_box)
        
        # Password input
        password_box = BoxLayout(orientation='horizontal', padding=10, spacing=10)
        password_box.add_widget(Label(text="Password:", font_size=20, size_hint=(0.3, 1)))
        self.password_input = TextInput(password=True, size_hint=(0.7, 1))
        password_box.add_widget(self.password_input)
        layout.add_widget(password_box)

        # Login button
        button_box = BoxLayout(orientation='horizontal', padding=10, spacing=10, size_hint=(1, 0.2))
        login_button = Button(text="Login", size_hint=(0.5, 1))
        login_button.bind(on_press=self.check_credentials)
        button_box.add_widget(login_button)

        # Back button
        back_button = Button(text="Back to Home", size_hint=(0.5, 1))
        back_button.bind(on_press=self.go_to_home)
        button_box.add_widget(back_button)

        layout.add_widget(button_box)
        self.add_widget(layout)

    def check_credentials(self, instance):
        username = self.username_input.text
        password = self.password_input.text
        if username == 'user123' and password == 'password123':
            self.manager.current = 'visuai'
        else:
            self.show_error_popup()

    def show_error_popup(self):
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_layout.add_widget(Label(text="Invalid username or password.", font_size=20))
        dismiss_button = Button(text="Dismiss", size_hint=(1, 0.2))
        popup_layout.add_widget(dismiss_button)
        
        popup = Popup(title="Login Error", content=popup_layout, size_hint=(0.8, 0.4))
        dismiss_button.bind(on_press=popup.dismiss)
        popup.open()

    def go_to_home(self, instance):
        self.manager.current = 'home'
