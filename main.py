from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
import threading
import os
import re

# Handle Android imports gracefully
try:
    from android.permissions import request_permissions, Permission, check_permission
    from android.storage import primary_external_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False
    print("Not running on Android - permissions skipped")

from downloader import download_video, download_audio, get_available_formats
from debug import get_progress, clear_progress

class DownloaderApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.download_thread = None
        self.is_downloading = False
        self.current_url = ""
        
    def build(self):
        # Request Android permissions if on Android
        if ANDROID:
            request_permissions([
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.INTERNET
            ])
        
        # Set window background color
        Window.clearcolor = (0.95, 0.95, 0.95, 1)
        
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=15, spacing=12)
        
        # Header with gradient background
        header_layout = BoxLayout(size_hint=(1, 0.12), padding=10)
        with header_layout.canvas.before:
            Color(0.2, 0.4, 0.8, 1)
            self.header_rect = Rectangle(size=header_layout.size, pos=header_layout.pos)
        header_layout.bind(size=self._update_rect, pos=self._update_rect)
        
        title = Label(
            text='[b]YouTube Downloader[/b]',
            markup=True,
            size_hint=(1, 1),
            font_size='26sp',
            color=(1, 1, 1, 1)
        )
        header_layout.add_widget(title)
        layout.add_widget(header_layout)
        
        # Spacer
        layout.add_widget(Label(size_hint=(1, 0.02)))
        
        # URL Input Section
        url_label = Label(
            text='Enter YouTube URL:',
            size_hint=(1, 0.06),
            font_size='16sp',
            color=(0.2, 0.2, 0.2, 1),
            halign='left'
        )
        url_label.bind(size=url_label.setter('text_size'))
        layout.add_widget(url_label)
        
        self.url_input = TextInput(
            hint_text='https://youtube.com/watch?v=...',
            multiline=False,
            size_hint=(1, 0.1),
            font_size='14sp',
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            padding=[10, 10]
        )
        self.url_input.bind(text=self.on_url_change)
        layout.add_widget(self.url_input)
        
        # Download type selector
        type_label = Label(
            text='Download Type:',
            size_hint=(1, 0.06),
            font_size='16sp',
            color=(0.2, 0.2, 0.2, 1),
            halign='left'
        )
        type_label.bind(size=type_label.setter('text_size'))
        layout.add_widget(type_label)
        
        self.type_spinner = Spinner(
            text='Video (MP4)',
            values=('Video (MP4)', 'Audio Only (MP3)'),
            size_hint=(1, 0.09),
            font_size='15sp',
            background_color=(1, 1, 1, 1)
        )
        self.type_spinner.bind(text=self.on_type_change)
        layout.add_widget(self.type_spinner)
        
        # Resolution selector (initially visible)
        self.res_label = Label(
            text='Video Quality:',
            size_hint=(1, 0.06),
            font_size='16sp',
            color=(0.2, 0.2, 0.2, 1),
            halign='left'
        )
        self.res_label.bind(size=self.res_label.setter('text_size'))
        layout.add_widget(self.res_label)
        
        self.res_spinner = Spinner(
            text='1080p (Full HD)',
            values=('4320p (8K)', '2160p (4K)', '1440p (2K)', '1080p (Full HD)', '720p (HD)'),
            size_hint=(1, 0.09),
            font_size='15sp',
            background_color=(1, 1, 1, 1)
        )
        layout.add_widget(self.res_spinner)
        
        # Fetch formats button
        self.fetch_btn = Button(
            text='🔍 Fetch Available Formats',
            size_hint=(1, 0.09),
            background_color=(0.3, 0.6, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size='15sp',
            bold=True
        )
        self.fetch_btn.bind(on_press=self.fetch_formats)
        layout.add_widget(self.fetch_btn)
        
        # Download button
        self.download_btn = Button(
            text='⬇ Start Download',
            size_hint=(1, 0.11),
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size='18sp',
            bold=True
        )
        self.download_btn.bind(on_press=self.start_download)
        layout.add_widget(self.download_btn)
        
        # Progress section
        progress_label = Label(
            text='Download Progress:',
            size_hint=(1, 0.05),
            font_size='14sp',
            color=(0.2, 0.2, 0.2, 1),
            halign='left'
        )
        progress_label.bind(size=progress_label.setter('text_size'))
        layout.add_widget(progress_label)
        
        self.progress_bar = ProgressBar(
            max=100,
            size_hint=(1, 0.06),
            value=0
        )
        layout.add_widget(self.progress_bar)
        
        self.progress_label = Label(
            text='0%',
            size_hint=(1, 0.05),
            font_size='14sp',
            color=(0.3, 0.3, 0.3, 1)
        )
        layout.add_widget(self.progress_label)
        
        # Status label (scrollable)
        status_container_label = Label(
            text='Status:',
            size_hint=(1, 0.04),
            font_size='14sp',
            color=(0.2, 0.2, 0.2, 1),
            halign='left'
        )
        status_container_label.bind(size=status_container_label.setter('text_size'))
        layout.add_widget(status_container_label)
        
        scroll = ScrollView(size_hint=(1, 0.2))
        self.status_label = Label(
            text='Ready to download. Enter a YouTube URL above.',
            size_hint_y=None,
            text_size=(Window.width - 40, None),
            halign='left',
            valign='top',
            color=(0.1, 0.1, 0.1, 1),
            font_size='13sp',
            padding=[10, 10]
        )
        self.status_label.bind(texture_size=self.status_label.setter('size'))
        scroll.add_widget(self.status_label)
        layout.add_widget(scroll)
        
        # Schedule progress updates
        Clock.schedule_interval(self.update_progress, 0.3)
        
        return layout
    
    def _update_rect(self, instance, value):
        """Update rectangle size for header background"""
        self.header_rect.pos = instance.pos
        self.header_rect.size = instance.size
    
    def on_url_change(self, instance, value):
        """Track URL changes"""
        self.current_url = value.strip()
    
    def on_type_change(self, spinner, text):
        """Show/hide resolution selector based on download type"""
        if text == 'Audio Only (MP3)':
            self.res_label.opacity = 0
            self.res_label.disabled = True
            self.res_spinner.opacity = 0
            self.res_spinner.disabled = True
            self.fetch_btn.opacity = 0
            self.fetch_btn.disabled = True
        else:
            self.res_label.opacity = 1
            self.res_label.disabled = False
            self.res_spinner.opacity = 1
            self.res_spinner.disabled = False
            self.fetch_btn.opacity = 1
            self.fetch_btn.disabled = False
    
    def show_popup(self, title, message):
        """Show a popup message"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, size_hint=(1, 0.8)))
        close_btn = Button(text='OK', size_hint=(1, 0.2))
        content.add_widget(close_btn)
        
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def fetch_formats(self, instance):
        """Fetch available formats for the video"""
        url = self.current_url
        if not url:
            self.show_popup('Error', 'Please enter a YouTube URL first')
            return
        
        self.status_label.text = 'Fetching available formats...'
        self.fetch_btn.disabled = True
        self.fetch_btn.text = '⏳ Fetching...'
        
        def fetch_thread():
            try:
                formats = get_available_formats(url)
                if formats:
                    res_map = {
                        "7680x4320": "4320p (8K)",
                        "3840x2160": "2160p (4K)",
                        "2560x1440": "1440p (2K)",
                        "1920x1080": "1080p (Full HD)",
                        "1280x720": "720p (HD)"
                    }
                    values = [res_map.get(res, res) for res in formats.keys()]
                    Clock.schedule_once(lambda dt: self.update_resolutions(values), 0)
                    Clock.schedule_once(
                        lambda dt: setattr(self.status_label, 'text', 
                                         f'✓ Found {len(formats)} available quality options'), 0
                    )
                else:
                    Clock.schedule_once(
                        lambda dt: setattr(self.status_label, 'text', 
                                         '⚠ Could not fetch formats. Using default options.'), 0
                    )
            except Exception as e:
                Clock.schedule_once(
                    lambda dt: setattr(self.status_label, 'text', 
                                     f'Error fetching formats: {str(e)}'), 0
                )
            finally:
                Clock.schedule_once(lambda dt: setattr(self.fetch_btn, 'disabled', False), 0)
                Clock.schedule_once(lambda dt: setattr(self.fetch_btn, 'text', '🔍 Fetch Available Formats'), 0)
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def update_resolutions(self, values):
        """Update resolution spinner values"""
        if values:
            self.res_spinner.values = values
            self.res_spinner.text = values[0] if values else '1080p (Full HD)'
    
    def start_download(self, instance):
        """Start the download in a background thread"""
        if self.is_downloading:
            self.show_popup('Download in Progress', 'A download is already running. Please wait.')
            return
        
        url = self.current_url
        if not url:
            self.show_popup('Error', 'Please enter a YouTube URL')
            return
        
        # Validate URL
        if not ('youtube.com' in url or 'youtu.be' in url):
            self.show_popup('Invalid URL', 'Please enter a valid YouTube URL')
            return
        
        clear_progress()
        self.progress_bar.value = 0
        self.progress_label.text = '0%'
        self.download_btn.disabled = True
        self.download_btn.text = '⏳ Downloading...'
        self.download_btn.background_color = (0.6, 0.6, 0.6, 1)
        self.is_downloading = True
        
        download_type = self.type_spinner.text
        
        # Extract resolution from spinner text (e.g., "1080p (Full HD)" -> "1920x1080")
        res_map = {
            "4320p (8K)": "7680x4320",
            "2160p (4K)": "3840x2160",
            "1440p (2K)": "2560x1440",
            "1080p (Full HD)": "1920x1080",
            "720p (HD)": "1280x720"
        }
        selected_res = res_map.get(self.res_spinner.text, "1920x1080")
        
        def download_thread():
            try:
                if download_type == 'Audio Only (MP3)':
                    result = download_audio(url)
                else:
                    result = download_video(url, selected_res=selected_res)
                
                Clock.schedule_once(lambda dt: self.download_complete(result), 0)
            except Exception as e:
                Clock.schedule_once(
                    lambda dt: self.download_complete(f'Error: {str(e)}'), 0
                )
        
        self.download_thread = threading.Thread(target=download_thread, daemon=True)
        self.download_thread.start()
        self.status_label.text = 'Download started... Please wait.'
    
    def download_complete(self, result):
        """Handle download completion"""
        self.status_label.text = result
        self.download_btn.disabled = False
        self.download_btn.text = '⬇ Start Download'
        self.download_btn.background_color = (0.2, 0.7, 0.3, 1)
        self.is_downloading = False
        
        if 'complete' in result.lower() or 'success' in result.lower():
            self.progress_bar.value = 100
            self.progress_label.text = '100%'
            self.show_popup('Success! 🎉', result)
        else:
            self.show_popup('Download Failed', result)
    
    def update_progress(self, dt):
        """Update progress bar and status from progress file"""
        if not self.is_downloading:
            return
        
        progress_text = get_progress()
        if progress_text and progress_text != 'Waiting...':
            self.status_label.text = progress_text
            
            # Extract percentage if present
            match = re.search(r'(\d+\.?\d*)%', progress_text)
            if match:
                try:
                    percent = float(match.group(1))
                    self.progress_bar.value = min(percent, 100)
                    self.progress_label.text = f'{percent:.1f}%'
                except ValueError:
                    pass

if __name__ == '__main__':
    DownloaderApp().run()
