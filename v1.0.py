import asyncio
import json
import os
import time
import threading
import subprocess
import warnings
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import speech_recognition as sr
from shazamio import Shazam

# Suppress warnings
warnings.filterwarnings("ignore")

HISTORY_FILE = "song_history.json"
SONG_DIRECTORY = "Downloaded_Songs"
LISTENING = False
last_song = {"title": "", "artist": "", "timestamp": 0}
last_recognition_time = 0  # Track last recognition time

if not os.path.exists(SONG_DIRECTORY):
    os.makedirs(SONG_DIRECTORY)

def save_to_history(song_data):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            try:
                history = json.load(file)
            except json.JSONDecodeError:
                history = []
    history.append(song_data)
    with open(HISTORY_FILE, "w") as file:
        json.dump(history, file, indent=4)

async def recognize_song(file_path):
    global last_song, last_recognition_time
    shazam = Shazam()
    try:
        out = await shazam.recognize_song(file_path)
        if 'track' in out:
            song = out['track']
            title = song.get('title', 'Unknown')
            artist = song.get('subtitle', 'Unknown')
            current_time = time.time()
            
            # If the same song is playing, wait at least 35 seconds before adding it again
            if last_song["title"] == title and last_song["artist"] == artist:
                if current_time - last_recognition_time < 35:
                    update_status(f"Skipping duplicate: {title} by {artist}")
                    return
            
            # Update last recognized song and time
            song_data = {"title": title, "artist": artist, "recognized_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            last_song.update({"title": title, "artist": artist, "timestamp": current_time})
            last_recognition_time = current_time  # Update recognition time

            add_to_gui(song_data)
            save_to_history(song_data)
        else:
            update_status("No match found.")
    except Exception as e:
        update_status(f"Error: {e}")

def record_audio(duration=10):
    recognizer = sr.Recognizer()
    mic = sr.Microphone(sample_rate=44100)
    
    with mic as source:
        update_status("Recording audio...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.record(source, duration=duration)
    
    wav_file = "recorded_audio.wav"
    with open(wav_file, "wb") as f:
        f.write(audio.get_wav_data())
    return wav_file

def listen_continuously():
    global LISTENING, last_recognition_time
    update_status("Listening for music...")
    while LISTENING:
        audio_file = record_audio()
        asyncio.run(recognize_song(audio_file))
        
        # Check if 10 seconds have passed with no new song detected
        if time.time() - last_recognition_time >= 10:
            last_song["title"], last_song["artist"] = "", ""  # Reset last song
        time.sleep(2)

def start_listening():
    global LISTENING
    if not LISTENING:
        LISTENING = True
        threading.Thread(target=listen_continuously, daemon=True).start()
        update_status("Started listening!")

def stop_listening():
    global LISTENING
    LISTENING = False
    update_status("Stopped listening.")

def update_status(message):
    status_label.config(text=message)

def add_to_gui(song_data):
    history_list.insert("", "end", values=(song_data["title"], song_data["artist"], song_data["recognized_at"]))

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            try:
                history = json.load(file)
                for song in history:
                    add_to_gui(song)
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Failed to load history.")

def export_history():
    if os.path.exists(HISTORY_FILE):
        messagebox.showinfo("Export", f"History saved in {HISTORY_FILE}")
    else:
        messagebox.showwarning("Export", "No history found.")

def download_song():
    selected_item = history_list.selection()
    if not selected_item:
        messagebox.showwarning("Download", "Please select a song first!")
        return

    song_values = history_list.item(selected_item, "values")
    song_title = song_values[0]
    artist_name = song_values[1]

    # Ensure the download folder exists
    os.makedirs(SONG_DIRECTORY, exist_ok=True)

    update_status(f"Downloading {song_title}...")

    try:
        # Auto-select choice "1" and ignore errors
        command = f'echo 1 | ytmdl "{song_title} {artist_name}" -o "{SONG_DIRECTORY}" --ignore-errors --format mp3 --skip-meta'
        subprocess.run(command, shell=True, check=True)
        
        update_status(f"Downloaded: {song_title}")
        messagebox.showinfo("Download", f"{song_title} downloaded successfully in {SONG_DIRECTORY}!")
    except subprocess.CalledProcessError as e:
        update_status(f"Download failed: {e}")
        messagebox.showerror("Error", f"Failed to download {song_title}")

def filter_songs():
    filter_param = filter_param_var.get()
    filter_value = filter_value_var.get()
    
    for item in history_list.get_children():
        history_list.delete(item)
    
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            try:
                history = json.load(file)
                filtered_history = []
                for song in history:
                    if filter_param == "Title" and filter_value.lower() in song['title'].lower():
                        filtered_history.append(song)
                    elif filter_param == "Artist" and filter_value.lower() in song['artist'].lower():
                        filtered_history.append(song)
                    elif filter_param == "Time" and filter_value in song['recognized_at']:
                        filtered_history.append(song)
                
                for song in filtered_history:
                    add_to_gui(song)
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Failed to load history.")

def clear_filter():
    filter_value_var.set("")
    for item in history_list.get_children():
        history_list.delete(item)
    load_history()

def clear_sort():
    sort_var.set("Title")
    sort_songs()

def sort_songs():
    sort_option = sort_var.get()
    
    items = history_list.get_children()
    song_data = [history_list.item(item, "values") for item in items]
    
    if sort_option == "Title":
        song_data.sort(key=lambda x: x[0].lower())
    elif sort_option == "Artist":
        song_data.sort(key=lambda x: x[1].lower())
    elif sort_option == "Time":
        song_data.sort(key=lambda x: datetime.strptime(x[2], "%Y-%m-%d %H:%M:%S"))
    
    for item in items:
        history_list.delete(item)
    
    for song in song_data:
        history_list.insert("", "end", values=song)

def update_filter_values(*args):
    filter_param = filter_param_var.get()
    filter_value_var.set("")
    filter_value_dropdown['values'] = get_unique_values(filter_param)

def get_unique_values(filter_param):
    unique_values = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            try:
                history = json.load(file)
                for song in history:
                    if filter_param == "Title":
                        unique_values.add(song['title'])
                    elif filter_param == "Artist":
                        unique_values.add(song['artist'])
                    elif filter_param == "Time":
                        unique_values.add(song['recognized_at'])
            except json.JSONDecodeError:
                pass
    return sorted(unique_values)

root = tk.Tk()
root.title("Background Song Identifier")
root.geometry("800x450")
root.resizable(False, False)

frame = tk.Frame(root)
frame.pack(pady=10)
button_style = {"bg": "lightgray", "fg": "black", "width": 15}

start_btn = tk.Button(frame, text="Start Listening", command=start_listening, **button_style)
start_btn.grid(row=0, column=0, padx=5)

stop_btn = tk.Button(frame, text="Stop Listening", command=stop_listening, **button_style)
stop_btn.grid(row=0, column=1, padx=5)

export_btn = tk.Button(frame, text="Export History", command=export_history, **button_style)
export_btn.grid(row=0, column=2, padx=5)

download_btn = tk.Button(root, text="Download Selected Song", command=download_song, **button_style)
download_btn.pack(pady=5)

status_label = tk.Label(root, text="Press 'Start Listening' to begin", fg="blue")
status_label.pack(pady=10)

# Add search bar
search_frame = tk.Frame(root)
search_frame.pack(pady=5)

tk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
search_var = tk.StringVar()
search_entry = tk.Entry(search_frame, textvariable=search_var)
search_entry.pack(side=tk.LEFT, padx=5)
search_button = tk.Button(search_frame, text="Search", command=filter_songs)
search_button.pack(side=tk.LEFT, padx=5)

# Add filter options
filter_frame = tk.Frame(root)
filter_frame.pack(pady=5)

tk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT, padx=5)
filter_param_var = tk.StringVar(value="Title")
filter_param_dropdown = ttk.Combobox(filter_frame, textvariable=filter_param_var, values=["Title", "Artist", "Time"])
filter_param_dropdown.pack(side=tk.LEFT, padx=5)
filter_param_dropdown.bind("<<ComboboxSelected>>", update_filter_values)

filter_value_var = tk.StringVar()
filter_value_dropdown = ttk.Combobox(filter_frame, textvariable=filter_value_var)
filter_value_dropdown.pack(side=tk.LEFT, padx=5)

filter_button = tk.Button(filter_frame, text="Filter", command=filter_songs)
filter_button.pack(side=tk.LEFT, padx=5)

clear_filter_button = tk.Button(filter_frame, text="Clear Filter", command=clear_filter)
clear_filter_button.pack(side=tk.LEFT, padx=5)

# Add sorting dropdown
sort_frame = tk.Frame(root)
sort_frame.pack(pady=5)

tk.Label(sort_frame, text="Sort by:").pack(side=tk.LEFT, padx=5)
sort_var = tk.StringVar(value="Title")
sort_dropdown = ttk.Combobox(sort_frame, textvariable=sort_var, values=["Title", "Artist", "Time"])
sort_dropdown.pack(side=tk.LEFT, padx=5)
sort_button = tk.Button(sort_frame, text="Sort", command=sort_songs)
sort_button.pack(side=tk.LEFT, padx=5)

clear_sort_button = tk.Button(sort_frame, text="Clear Sort", command=clear_sort)
clear_sort_button.pack(side=tk.LEFT, padx=5)

columns = ("Title", "Artist", "Time")
history_list = ttk.Treeview(root, columns=columns, show="headings", height=10)
for col in columns:
    history_list.heading(col, text=col)
    history_list.column(col, width=180)
history_list.pack(pady=10)

load_history()
root.mainloop()