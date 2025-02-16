import asyncio
import json
import os
import time
import threading
import subprocess
import warnings
from datetime import datetime
from shazamio import Shazam
import speech_recognition as sr

# Suppress warnings
warnings.filterwarnings("ignore")

HISTORY_FILE = "song_history.json"
SONG_DIRECTORY = "Downloaded_Songs"
LISTENING = False
last_song = {"title": "", "artist": "", "timestamp": 0}
last_recognition_time = 0  # Track last recognition time

if not os.path.exists(SONG_DIRECTORY):
    os.makedirs(SONG_DIRECTORY)

def get_time_category(timestamp):
    """Categorize time into morning, afternoon, evening, or night."""
    hour = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").hour
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    else:
        return "Night"

def get_day_of_week(timestamp):
    """Get the day of the week from a timestamp."""
    return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%A")

def save_to_history(song_data):
    """Save song data to history file."""
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

def is_song_already_detected(title, artist):
    """Check if the song is already in the history."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            try:
                history = json.load(file)
                for song in history:
                    if song["title"].lower() == title.lower() and song["artist"].lower() == artist.lower():
                        return True
            except json.JSONDecodeError:
                pass
    return False

def download_song(title, artist):
    """Download the song using ytmdl."""
    print(f"Downloading {title} by {artist}...")
    try:
        # Auto-select choice "1" and ignore errors
        command = f'echo 1 | ytmdl "{title} {artist}" -o "{SONG_DIRECTORY}" --ignore-errors --format mp3 --skip-meta'
        subprocess.run(command, shell=True, check=True)
        print(f"Downloaded: {title} by {artist}")
    except subprocess.CalledProcessError as e:
        print(f"Download failed: {e}")

async def recognize_song(file_path):
    """Recognize a song using Shazam."""
    global last_song, last_recognition_time
    shazam = Shazam()
    try:
        out = await shazam.recognize_song(file_path)
        if 'track' in out:
            song = out['track']
            title = song.get('title', 'Unknown')
            artist = song.get('subtitle', 'Unknown')
            current_time = time.time()

            # Update last recognized song and time
            recognized_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            time_category = get_time_category(recognized_at)
            day_of_week = get_day_of_week(recognized_at)
            song_data = {
                "title": title,
                "artist": artist,
                "recognized_at": recognized_at,
                "date": recognized_at.split()[0],
                "time": recognized_at.split()[1],
                "time_category": time_category,
                "day_of_week": day_of_week
            }
            last_song.update({"title": title, "artist": artist, "timestamp": current_time})
            last_recognition_time = current_time  # Update recognition time

            # Check if the song is already detected
            if not is_song_already_detected(title, artist):
                # Download the song if it's new
                download_song(title, artist)
            
            # Save the song to history
            save_to_history(song_data)
        else:
            print("No match found.")
    except Exception as e:
        print(f"Error: {e}")

def record_audio(duration=10):
    """Record audio from the microphone."""
    recognizer = sr.Recognizer()
    mic = sr.Microphone(sample_rate=44100)
    
    with mic as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.record(source, duration=duration)
    
    wav_file = "recorded_audio.wav"
    with open(wav_file, "wb") as f:
        f.write(audio.get_wav_data())
    return wav_file

def listen_continuously():
    """Continuously listen for music."""
    global LISTENING, last_recognition_time
    print("Listening for music...")
    while LISTENING:
        audio_file = record_audio()
        asyncio.run(recognize_song(audio_file))
        
        # Check if 10 seconds have passed with no new song detected
        if time.time() - last_recognition_time >= 10:
            last_song["title"], last_song["artist"] = "", ""  # Reset last song
        time.sleep(2)

def start_listening():
    """Start the listening process."""
    global LISTENING
    if not LISTENING:
        LISTENING = True
        threading.Thread(target=listen_continuously, daemon=True).start()
        print("Started listening!")

def stop_listening():
    """Stop the listening process."""
    global LISTENING
    LISTENING = False
    print("Stopped listening.")

if __name__ == "__main__":
    # Start listening for songs
    start_listening()

    # Keep the main thread alive
    while True:
        time.sleep(1)