from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from home_screen import HomeScreen
from login_screen import LoginScreen
from visuai_screen import VisuAI

class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(VisuAI(name='visuai'))
        return sm

if __name__ == '__main__':
    MyApp().run()
