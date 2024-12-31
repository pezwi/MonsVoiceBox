import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import pyttsx3
import subprocess
import shutil
import zipfile
import sys
import requests

# For Android, we would typically import PyDroid-related modules (but on desktop, we'll use pyttsx3)
try:
    import android
except ImportError:
    android = None

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mons Voice Box 1.0.2")
        self.root.geometry("600x600")  # Increased size for tablet use

        self.receiver_ip = tk.StringVar(value="0.0.0.0")  # Default to listen on all interfaces
        self.receiver_port = tk.IntVar(value=12345)
        self.target_ip = tk.StringVar(value="192.168.1.101")
        self.target_port = tk.IntVar(value=12345)
        self.is_listening = False
        self.last_message = ""  # Stores the last sent message

        self.check_for_updates_button()

        self.tts_engine = pyttsx3.init()  # For desktop TTS

        self.create_tabs()
        self.auto_start_listening()

    def check_for_updates_button(self):
        # Create an "Update" button to check for updates
        update_button = tk.Button(self.root, text="Check for Updates", command=self.check_for_updates, width=20, height=2, bg="blue")
        update_button.pack(pady=10)

    def check_for_updates(self, event=None):
        import requests
        from tkinter import messagebox
        import os
        import zipfile
        import shutil

        repo_url = "https://api.github.com/repos/pezwi/MonsVoiceBox/releases/latest"
        self.current_version = "v1.0.0"  # Replace with your app's actual current version

        try:
            # Fetch release information from GitHub
            response = requests.get(repo_url)
            response.raise_for_status()
            release_data = response.json()

            # Extract version and download URL
            remote_version = release_data.get("tag_name")
            download_url = release_data.get("zipball_url")

            if not remote_version or not download_url:
                raise ValueError("Release data missing 'tag_name' or 'zipball_url'.")

            # Strip "v" prefix for comparison
            current_version_clean = self.current_version.lstrip("v")
            remote_version_clean = remote_version.lstrip("v")

            # Compare versions
            if remote_version_clean > current_version_clean:
                messagebox.showinfo(
                    "Update Available",
                    f"A new version ({remote_version}) is available. Downloading now..."
                )
                self.download_and_install_update(download_url)
            else:
                messagebox.showinfo("No Updates", "You are using the latest version.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Update Error", f"Network error: {e}")
        except ValueError as e:
            messagebox.showerror("Update Error", f"Invalid response data: {e}")
        except Exception as e:
            messagebox.showerror("Update Error", f"An unexpected error occurred: {e}")

    def download_and_install_update(self, download_url):
        import os
        import zipfile
        import shutil
        from tkinter import messagebox

        try:
            # Step 1: Download the ZIP file
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            zip_path = "MonsVoiceBox-1.0.1.zip"
            with open(zip_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            # Step 2: Extract the ZIP file
            extract_path = "C:/temp"
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # Step 3: Replace current files with new files
            current_dir = os.path.dirname(os.path.abspath(__file__))
            for item in os.listdir(extract_path):
                source_path = os.path.join(extract_path, item)
                dest_path = os.path.join(current_dir, item)

                if os.path.isdir(source_path):
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
                    shutil.move(source_path, dest_path)
                else:
                    shutil.move(source_path, dest_path)

            # Step 4: Clean up
            os.remove(zip_path)
            shutil.rmtree(extract_path)

            # Step 5: Restart the application
            self.restart_app()
        except Exception as e:
            messagebox.showerror("Update Error", f"Failed to install update: {e}")

    def restart_app(self):
        import os
        import sys
        from tkinter import messagebox

        try:
            # Relaunch the application
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            messagebox.showerror("Restart Error", f"Failed to restart the application: {e}")

    def create_tabs(self):
        # Create tabbed interface
        notebook = ttk.Notebook(self.root)
        self.home_tab = ttk.Frame(notebook)
        self.settings_tab = ttk.Frame(notebook)
        self.android_tab = ttk.Frame(notebook)

        notebook.add(self.home_tab, text="Home")
        notebook.add(self.settings_tab, text="Settings")
        notebook.add(self.android_tab, text="Android TTS")  # New Android TTS tab
        notebook.pack(expand=True, fill="both")

        # Build each tab
        self.setup_home_tab()
        self.setup_settings_tab()
        self.setup_android_tab()  # New Android TTS tab setup

    def setup_home_tab(self):
        # Home Tab UI
        tk.Label(self.home_tab, text="Message to Send:").pack(pady=5)

        # Input and Send Buttons
        message_frame = tk.Frame(self.home_tab)
        message_frame.pack(pady=5)

        self.message_entry = tk.Entry(message_frame, width=40)
        self.message_entry.pack(side=tk.LEFT, padx=5)

        # Bind Enter key to send message
        self.message_entry.bind("<Return>", lambda event: self.send_message())  # This binds Enter key to send message

        # Send and Resend Buttons (Grey)
        tk.Button(message_frame, text="Send Message", command=self.send_message, width=15, height=2, bg="grey").pack(side=tk.LEFT, padx=5, pady=10)
        tk.Button(message_frame, text="Resend Last Message", command=self.resend_last_message, width=15, height=2, bg="grey").pack(side=tk.LEFT, padx=5, pady=10)

        # Notifications Section
        notification_frame = tk.LabelFrame(self.home_tab, text="Notifications", padx=10, pady=10, borderwidth=2, relief="groove")
        notification_frame.pack(pady=10, fill="x")

        # Notification Buttons (Grouped by Color)
        tk.Button(notification_frame, text="Ring Ring", command=lambda: self.send_predefined_message("Ring Ring"), width=15, height=2, bg="green").grid(row=1, column=0, padx=5, pady=5)
        tk.Button(notification_frame, text="Nudge Chris", command=lambda: self.send_notification_to_chris, width=15, height=2, bg="red").grid(row=0, column=0, padx=5, pady=5)
        tk.Button(notification_frame, text="Tea Inquiry", command=lambda: self.send_tea_inquiry, width=15, height=2, bg="red").grid(row=0, column=1, padx=5, pady=5)
        tk.Button(notification_frame, text="Yes", command=lambda: self.send_predefined_message("Yes"), width=15, height=2, bg="green").grid(row=1, column=0, padx=5, pady=5)
        tk.Button(notification_frame, text="No", command=lambda: self.send_predefined_message("No"), width=15, height=2, bg="green").grid(row=1, column=1, padx=5, pady=5)
        tk.Button(notification_frame, text="Hello", command=lambda: self.send_predefined_message("Hello"), width=15, height=2, bg="green").grid(row=1, column=2, padx=5, pady=5)

    def setup_settings_tab(self):
        # Settings Tab UI
        tk.Label(self.settings_tab, text="Receiver Settings").pack(pady=5)
        tk.Label(self.settings_tab, text="IP Address:").pack()
        tk.Entry(self.settings_tab, textvariable=self.receiver_ip).pack()
        tk.Label(self.settings_tab, text="Port:").pack()
        tk.Entry(self.settings_tab, textvariable=self.receiver_port).pack()

        tk.Label(self.settings_tab, text="Sender Settings").pack(pady=5)
        tk.Label(self.settings_tab, text="Target IP Address:").pack()
        tk.Entry(self.settings_tab, textvariable=self.target_ip).pack()
        tk.Label(self.settings_tab, text="Target Port:").pack()
        tk.Entry(self.settings_tab, textvariable=self.target_port).pack()

        # Listening Button
        self.listen_button = tk.Button(self.settings_tab, text="Stop Listening", command=self.toggle_listening, width=20, height=2)
        self.listen_button.pack(pady=10)

    def setup_android_tab(self):
        # Android TTS Tab UI
        tk.Label(self.android_tab, text="Message to Send to Android:").pack(pady=5)

        # Input and Send Buttons for Android
        android_message_frame = tk.Frame(self.android_tab)
        android_message_frame.pack(pady=5)

        self.android_message_entry = tk.Entry(android_message_frame, width=40)
        self.android_message_entry.pack(side=tk.LEFT, padx=5)

        # Bind Enter key to send message
        self.android_message_entry.bind("<Return>", lambda event: self.send_message_android())

        # Send Button
        tk.Button(android_message_frame, text="Send Message to Android", command=self.send_message_android, width=20, height=2).pack(side=tk.LEFT, padx=5, pady=10)

    def send_message(self):
        message = self.message_entry.get()
        self.send_message_to_receiver(message)

    def resend_last_message(self):
        if self.last_message:
            print(f"Resending last message: {self.last_message}")
            self.send_message_to_receiver(self.last_message)
        else:
            print("No message to resend.")


    def send_predefined_message(self, message):
        self.send_message_to_receiver(message)

    def send_message_android(self):
        message = self.android_message_entry.get()
        self.send_message_to_android(message)

    def send_message_to_receiver(self, message):
        if self.is_listening:
            try:
                # Send message over UDP
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(message.encode('utf-8'), (self.target_ip.get(), self.target_port.get()))
            except Exception as e:
                print(f"Error sending message: {e}")
            finally:
                sock.close()

    def send_message_to_android(self, message):
        if android:
            # Send the message to the Android device using the pyjnius interface or the android API directly.
            android.tts.say(message)
        else:
            print(f"Android TTS is not available. Message: {message}")

    def toggle_listening(self):
        self.is_listening = not self.is_listening
        if self.is_listening:
            self.listen_button.config(text="Stop Listening")
            # Start listening thread
            listening_thread = threading.Thread(target=self.listen_for_messages)
            listening_thread.daemon = True
            listening_thread.start()
        else:
            self.listen_button.config(text="Start Listening")

    def listen_for_messages(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((self.receiver_ip.get(), self.receiver_port.get()))
            while self.is_listening:
                data, addr = sock.recvfrom(1024)  # Buffer size
                message = data.decode('utf-8')
                if message and message != self.last_message:  # Prevent repetitive message processing
                    self.last_message = message
                    print(f"Received: {message}")
                    self.tts_engine.say(message)
                    self.tts_engine.runAndWait()  # Desktop TTS
        except Exception as e:
            print(f"Error listening for messages: {e}")
        finally:
            sock.close()

    def auto_start_listening(self):
        # Optionally auto-start listening when the app starts
        self.is_listening = True
        listening_thread = threading.Thread(target=self.listen_for_messages)
        listening_thread.daemon = True
        listening_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()
