import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import pyttsx3
import subprocess
import shutil
import zipfile
import sys

# For Android, we would typically import PyDroid-related modules (but on desktop, we'll use pyttsx3)
try:
    import android
except ImportError:
    android = None

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LAN Text-to-Speech App")
        self.root.geometry("600x600")  # Increased size for tablet use
        
        self.version_file = "version.json"  # A local version tracking file
        self.current_version = "1.0.0"  # Example current version
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

    def check_for_updates(self):
        # Check the current version against the latest release on GitHub
        try:
            # GitHub API URL for the latest release in your repository
            repo_url = "https://api.github.com/repos/{owner}/{repo}/releases/latest"  # Replace with your repo
            response = requests.get(repo_url)
            response.raise_for_status()  # Will raise an exception if the response code is not 200

            release_data = response.json()

            # Extract the latest release version
            remote_version = release_data.get("tag_name")

            if remote_version > self.current_version:
                # Update is available, ask user if they want to update
                response = messagebox.askyesno("Update Available", f"A new version ({remote_version}) is available. Do you want to update?")
                if response:
                    self.download_update(release_data)
            else:
                messagebox.showinfo("No Update", "You are running the latest version!")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to check for updates: {e}")

    def download_update(self, release_data):
        # Download the release asset (e.g., a ZIP file)
        try:
            # URL for the release asset (e.g., ZIP file)
            asset_url = release_data['assets'][0]['browser_download_url']  # Assumes the first asset is the ZIP file
            
            # Download the update file
            update_file = "new_version.zip"
            response = requests.get(asset_url)
            with open(update_file, 'wb') as f:
                f.write(response.content)

            # Install the update
            self.install_update(update_file)
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to download the update: {e}")

    def install_update(self, update_file):
        # Unzip and replace application files with the new version
        try:
            # Extract the ZIP file
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall("update_folder")

            # Replace the current application folder with the new one
            shutil.rmtree("current_app_folder")  # Remove old folder
            shutil.move("update_folder", "current_app_folder")  # Move the new folder to the app folder

            # Optionally, restart the app after update
            self.restart_app()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to install the update: {e}")

    def restart_app(self):
        # Restart the application with the new version
        try:
            subprocess.Popen([sys.executable, os.path.abspath(__file__)])  # Restart app
            self.root.quit()  # Close the current instance
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart the app: {e}")


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
        tk.Button(notification_frame, text="Nudge Chris", command=self.send_notification_to_chris, width=15, height=2, bg="red").grid(row=0, column=0, padx=5, pady=5)
        tk.Button(notification_frame, text="Tea Inquiry", command=self.send_tea_inquiry, width=15, height=2, bg="red").grid(row=0, column=1, padx=5, pady=5)
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
        message_frame = tk.Frame(self.android_tab)
        message_frame.pack(pady=5)

        self.android_message_entry = tk.Entry(message_frame, width=40)
        self.android_message_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(message_frame, text="Send to Android", command=self.send_to_android, width=15, height=2, bg="grey").pack(side=tk.LEFT, padx=5, pady=10)
        tk.Button(message_frame, text="Resend Last Message", command=self.resend_last_message, width=15, height=2, bg="grey").pack(side=tk.LEFT, padx=5, pady=10)

        # Notifications Section for Android
        notification_frame = tk.LabelFrame(self.android_tab, text="Android Notifications", padx=10, pady=10, borderwidth=2, relief="groove")
        notification_frame.pack(pady=10, fill="x")

        tk.Button(notification_frame, text="Nudge Chris", command=self.send_notification_to_chris, width=15, height=2, bg="red").grid(row=0, column=0, padx=5, pady=5)
        tk.Button(notification_frame, text="Tea Inquiry", command=self.send_tea_inquiry, width=15, height=2, bg="red").grid(row=0, column=1, padx=5, pady=5)
        tk.Button(notification_frame, text="Custom Notification", command=lambda: self.send_predefined_message("Custom Message"), width=15, height=2, bg="blue").grid(row=0, column=2, padx=5, pady=5)

    def send_to_android(self):
        message = self.android_message_entry.get()
        if not message:
            messagebox.showwarning("Warning", "Message cannot be empty!")
            return
        
        if android:
            android.tts.speak(message)  # Call TTS speak method in Android environment
            print(f"Sent to Android: {message}")
        else:
            messagebox.showwarning("Warning", "This feature is only available on Android!")

    def auto_start_listening(self):
        self.is_listening = True
        threading.Thread(target=self.start_tts_server, daemon=True).start()

    def toggle_listening(self):
        if not self.is_listening:
            self.is_listening = True
            self.listen_button.config(text="Stop Listening")
            threading.Thread(target=self.start_tts_server, daemon=True).start()
        else:
            self.is_listening = False
            self.listen_button.config(text="Start Listening")

    def start_tts_server(self):
        host = self.receiver_ip.get()
        port = self.receiver_port.get()
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((host, port))
            server_socket.listen()
            print(f"Listening on {host}:{port}...")
            
            while self.is_listening:
                try:
                    client_socket, addr = server_socket.accept()
                    print(f"Connection from {addr}")
                    
                    with client_socket:
                        data = client_socket.recv(1024).decode()
                        if data:
                            print(f"Received message: {data}")
                            self.tts_engine.say(data)
                            self.tts_engine.runAndWait()
                except Exception as e:
                    print(f"Error: {e}")
                    break

    def send_message(self):
        message = self.message_entry.get()
        if not message:
            messagebox.showwarning("Warning", "Message cannot be empty!")
            return
        
        ip = self.target_ip.get()
        port = self.target_port.get()
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port))
                s.sendall(message.encode())
            print(f"Message sent: {message}")
            self.last_message = message  # Save the message for later
            self.message_entry.delete(0, tk.END)  # Clear the input box
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}")

    def resend_last_message(self):
        if not self.last_message:
            messagebox.showwarning("Warning", "No message to resend!")
            return

        ip = self.target_ip.get()
        port = self.target_port.get()
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port))
                s.sendall(self.last_message.encode())
            print(f"Resent message: {self.last_message}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to resend message: {e}")

    def send_notification_to_chris(self):
        notification = "Hey Chris, wifey would like your attention for a moment."
        self.send_predefined_message(notification)

    def send_tea_inquiry(self):
        inquiry = "Hey Chris, Wifey would like to know if you want a cup of tea? Isn't she just amazing!"
        self.send_predefined_message(inquiry)

    def send_predefined_message(self, message):
        ip = self.target_ip.get()
        port = self.target_port.get()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port))
                s.sendall(message.encode())
            print(f"Predefined message sent: {message}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send predefined message: {e}")

# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()
