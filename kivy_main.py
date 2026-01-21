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
from android.permissions import request_permissions, Permission
from android.storage import primary_external_storage_path
import threading
import os
from downloader import download_video, download_audio, get_available_formats
from debug import get_progress, clear_progress

class DownloaderApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.download_thread = None
        self.is_downloading = False
        
    def build(self):
        # Request Android permissions
        request_permissions([
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.INTERNET
        ])
        
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(
            text='YouTube Downloader',
            size_hint=(1, 0.1),
            font_size='24sp',
            bold=True
        )
        layout.add_widget(title)
        
        # URL Input
        url_layout = BoxLayout(size_hint=(1, 0.12), spacing=5)
        url_layout.add_widget(Label(text='URL:', size_hint=(0.2, 1)))
        self.url_input = TextInput(
            hint_text='Enter YouTube URL',
            multiline=False,
            size_hint=(0.8, 1)
        )
        url_layout.add_widget(self.url_input)
        layout.add_widget(url_layout)
        
        # Download type selector
        type_layout = BoxLayout(size_hint=(1, 0.1), spacing=5)
        type_layout.add_widget(Label(text='Type:', size_hint=(0.3, 1)))
        self.type_spinner = Spinner(
            text='Video',
            values=('Video', 'Audio (MP3)'),
            size_hint=(0.7, 1)
        )
        self.type_spinner.bind(text=self.on_type_change)
        type_layout.add_widget(self.type_spinner)
        layout.add_widget(type_layout)
        
        # Resolution selector
        self.res_layout = BoxLayout(size_hint=(1, 0.1), spacing=5)
        self.res_layout.add_widget(Label(text='Resolution:', size_hint=(0.3, 1)))
        self.res_spinner = Spinner(
            text='1920x1080 (1080p)',
            values=('1920x1080 (1080p)', '1280x720 (720p)', '3840x2160 (4K)'),
            size_hint=(0.7, 1)
        )
        self.res_layout.add_widget(self.res_spinner)
        layout.add_widget(self.res_layout)
        
        # Fetch formats button
        self.fetch_btn = Button(
            text='Fetch Available Formats',
            size_hint=(1, 0.1),
            background_color=(0.2, 0.6, 0.8, 1)
        )
        self.fetch_btn.bind(on_press=self.fetch_formats)
        layout.add_widget(self.fetch_btn)
        
        # Download button
        self.download_btn = Button(
            text='Download',
            size_hint=(1, 0.12),
            background_color=(0.2, 0.8, 0.2, 1),
            font_size='18sp',
            bold=True
        )
        self.download_btn.bind(on_press=self.start_download)
        layout.add_widget(self.download_btn)
        
        # Progress bar
        self.progress_bar = ProgressBar(max=100, size_hint=(1, 0.08))
        layout.add_widget(self.progress_bar)
        
        # Status label (scrollable)
        scroll = ScrollView(size_hint=(1, 0.3))
        self.status_label = Label(
            text='Ready to download',
            size_hint_y=None,
            text_size=(Window.width - 20, None),
            halign='left',
            valign='top'
        )
        self.status_label.bind(texture_size=self.status_label.setter('size'))
        scroll.add_widget(self.status_label)
        layout.add_widget(scroll)
        
        # Schedule progress updates
        Clock.schedule_interval(self.update_progress, 0.5)
        
        return layout
    
    def on_type_change(self, spinner, text):
        """Show/hide resolution selector based on download type"""
        if text == 'Audio (MP3)':
            self.res_layout.opacity = 0
            self.res_layout.disabled = True
            self.fetch_btn.opacity = 0
            self.fetch_btn.disabled = True
        else:
            self.res_layout.opacity = 1
            self.res_layout.disabled = False
            self.fetch_btn.opacity = 1
            self.fetch_btn.disabled = False
    
    def fetch_formats(self, instance):
        """Fetch available formats for the video"""
        url = self.url_input.text.strip()
        if not url:
            self.status_label.text = 'Please enter a URL first'
            return
        
        self.status_label.text = 'Fetching available formats...'
        self.fetch_btn.disabled = True
        
        def fetch_thread():
            formats = get_available_formats(url)
            if formats:
                res_map = {
                    "7680x4320": "8K",
                    "3840x2160": "4K",
                    "2560x1440": "2K",
                    "1920x1080": "1080p",
                    "1280x720": "720p"
                }
                values = [f"{res} ({res_map.get(res, '')})" for res in formats.keys()]
                Clock.schedule_once(lambda dt: self.update_resolutions(values), 0)
                Clock.schedule_once(
                    lambda dt: setattr(self.status_label, 'text', 
                                     f'Found {len(formats)} formats'), 0
                )
            else:
                Clock.schedule_once(
                    lambda dt: setattr(self.status_label, 'text', 
                                     'Could not fetch formats. Using defaults.'), 0
                )
            Clock.schedule_once(lambda dt: setattr(self.fetch_btn, 'disabled', False), 0)
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def update_resolutions(self, values):
        """Update resolution spinner values"""
        if values:
            self.res_spinner.values = values
            self.res_spinner.text = values[0] if values else '1920x1080 (1080p)'
    
    def start_download(self, instance):
        """Start the download in a background thread"""
        if self.is_downloading:
            self.status_label.text = 'A download is already in progress'
            return
        
        url = self.url_input.text.strip()
        if not url:
            self.status_label.text = 'Please enter a URL'
            return
        
        clear_progress()
        self.progress_bar.value = 0
        self.download_btn.disabled = True
        self.is_downloading = True
        
        download_type = self.type_spinner.text
        selected_res = self.res_spinner.text.split(' ')[0] if download_type == 'Video' else None
        
        def download_thread():
            try:
                if download_type == 'Audio (MP3)':
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
        self.status_label.text = 'Download started...'
    
    def download_complete(self, result):
        """Handle download completion"""
        self.status_label.text = result
        self.download_btn.disabled = False
        self.is_downloading = False
        if 'complete' in result.lower():
            self.progress_bar.value = 100
    
    def update_progress(self, dt):
        """Update progress bar and status from progress file"""
        if not self.is_downloading:
            return
        
        progress_text = get_progress()
        if progress_text and progress_text != 'Waiting...':
            self.status_label.text = progress_text
            
            # Extract percentage if present
            import re
            match = re.search(r'(\d+\.?\d*)%', progress_text)
            if match:
                try:
                    percent = float(match.group(1))
                    self.progress_bar.value = min(percent, 100)
                except ValueError:
                    pass

if __name__ == '__main__':
    DownloaderApp().run()
