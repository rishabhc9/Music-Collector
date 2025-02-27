import asyncio
import json
import os
import time
import threading
import subprocess
import warnings
from datetime import datetime
from flask import Flask, render_template, send_from_directory, request, send_file
from shazamio import Shazam
import speech_recognition as sr
import zipfile
import io

from collections import defaultdict, Counter

# Suppress warnings
warnings.filterwarnings("ignore")

# for rpi
#HISTORY_FILE = "/home/pi/Desktop/Music-Collector/rpi_music_collector/song_history.json"
#SONG_DIRECTORY = "/home/pi/Desktop/Music-Collector/rpi_music_collector/Downloaded_Songs"

HISTORY_FILE = "song_history.json"
SONG_DIRECTORY = "Downloaded_Songs"

LISTENING = False
last_song = {"title": "", "artist": "", "timestamp": 0}
last_recognition_time = 0  # Track last recognition time

if not os.path.exists(SONG_DIRECTORY):
    os.makedirs(SONG_DIRECTORY)

app = Flask(__name__)

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
    print(f"Downloading {title} by {artist}...")
    try:
        # Use yt-dlp directly
        command = f'yt-dlp -x --audio-format mp3 -o "{SONG_DIRECTORY}/%(title)s.%(ext)s" "ytsearch1:{title} {artist}"'
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"Downloaded: {title} by {artist}")
        print("Command Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Download failed: {e}")
        print("Error Output:", e.stderr)

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

if not os.path.exists(SONG_DIRECTORY):
    os.makedirs(SONG_DIRECTORY)

# Helper functions (get_time_category, get_day_of_week, save_to_history, etc.) remain the same

@app.route('/')
def index():
    """Render the main page with song history and downloaded songs."""
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            try:
                history = json.load(file)
            except json.JSONDecodeError:
                history = []

    # Get list of downloaded songs
    downloaded_songs = os.listdir(SONG_DIRECTORY) if os.path.exists(SONG_DIRECTORY) else []

    return render_template('index.html', history=history, downloaded_songs=downloaded_songs)

@app.route('/wifi', methods=['GET', 'POST'])
def wifi_config():
    """Render and handle WiFi configuration."""
    if request.method == 'POST':
        ssid = request.form['ssid']
        password = request.form['password']
        
        # Update WiFi configuration (for Raspberry Pi)
        with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'a') as f:
            f.write(f'\nnetwork={{\n    ssid="{ssid}"\n    psk="{password}"\n}}\n')
        
        # Restart networking service
        subprocess.run(['sudo', 'systemctl', 'restart', 'networking'])
        
        return "WiFi configuration updated. Restarting network..."
    
    return render_template('wifi_config.html')

@app.route('/delete_songs', methods=['POST'])
def delete_songs():
    """Delete selected songs from the directory."""
    selected_songs = request.form.getlist('selected_songs')
    for song in selected_songs:
        os.remove(os.path.join(SONG_DIRECTORY, song))
    return "Selected songs deleted."

@app.route('/download_selected_songs', methods=['POST'])
def download_selected_songs():
    """Download selected songs as a ZIP file."""
    selected_songs = request.form.getlist('selected_songs')
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for song in selected_songs:
            zf.write(os.path.join(SONG_DIRECTORY, song), song)
    memory_file.seek(0)
    return send_file(memory_file, download_name='selected_songs.zip', as_attachment=True)

from collections import defaultdict
@app.route('/listening_stats')
def listening_stats():
    """Render the listening stats dashboard."""
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            try:
                history = json.load(file)
            except json.JSONDecodeError:
                history = []

    # Unique song tracking
    unique_songs = set()
    unique_artists = set()
    artist_count = defaultdict(int)
    date_count = defaultdict(int)
    time_category_count = defaultdict(int)
    day_of_week_count = defaultdict(int)
    month_count = defaultdict(int)

    for song in history:
        # Create a unique identifier for the song (title + all artists)
        song_key = (song.get("title", "Unknown"), song.get("artist", "Unknown"))

        # Ensure each unique song is counted only once
        if song_key not in unique_songs:
            unique_songs.add(song_key)

            # Properly separate artists using both ',' and '&'
            raw_artists = song.get("artist", "")
            artists = set(artist.strip() for artist in raw_artists.replace('&', ',').split(',') if artist.strip())

            # Add unique artists
            unique_artists.update(artists)

            # Count each artist for unique songs only
            for artist in artists:
                artist_count[artist] += 1

            # Count unique songs by date
            date = song.get("date", "Unknown")
            date_count[date] += 1

            # Extract month from date
            try:
                month = datetime.strptime(date, "%Y-%m-%d").strftime("%B %Y")  # Format: "January 2023"
                month_count[month] += 1
            except ValueError:
                month = "Unknown"

            # Count unique songs by time category
            time_category = song.get("time_category", "Unknown")
            time_category_count[time_category] += 1

            # Count unique songs by day of week
            day_of_week = song.get("day_of_week", "Unknown")
            day_of_week_count[day_of_week] += 1

    # Sort artists by song count for better visualization
    sorted_artists = sorted(artist_count.items(), key=lambda x: x[1], reverse=True)
    #print(f"sorted artists total {len(sorted_artists)}")
    top_25_artists = sorted_artists[:25]
    artist_names = [artist[0] for artist in top_25_artists]
    artist_values = [artist[1] for artist in top_25_artists]
    # Sort dates by song count
    sorted_dates = sorted(date_count.items(), key=lambda x: x[0])  # Sort by date
    date_labels = [date[0] for date in sorted_dates]
    date_values = [date[1] for date in sorted_dates]

    # Sort time categories by song count
    sorted_time_categories = sorted(time_category_count.items(), key=lambda x: x[0])  # Sort by time category
    time_category_labels = [time[0] for time in sorted_time_categories]
    time_category_values = [time[1] for time in sorted_time_categories]

    # Determine the most active day of the week
    most_active_day = max(day_of_week_count, key=day_of_week_count.get)

    # Get unique months for the filter dropdown
    unique_months = sorted(month_count.keys())

    # Ensure all data is JSON-serializable
    serializable_history = []
    for song in history:
        serializable_song = {
            "title": song.get("title", "Unknown"),
            "artist": song.get("artist", "Unknown"),
            "date": song.get("date", "Unknown"),
            "time_category": song.get("time_category", "Unknown"),
            "day_of_week": song.get("day_of_week", "Unknown")
        }
        serializable_history.append(serializable_song)

    return render_template('listening_stats.html', 
                           unique_songs=len(unique_songs), 
                           unique_artists=len(unique_artists), 
                           downloaded_songs=len(os.listdir(SONG_DIRECTORY)), 
                           most_active_day=most_active_day,
                           unique_months=unique_months,
                           artist_names=artist_names,
                           artist_values=artist_values,
                           date_labels=date_labels,
                           date_values=date_values,
                           time_category_labels=time_category_labels,
                           time_category_values=time_category_values,
                           history=serializable_history)


@app.route('/downloads/<filename>')
def download_file(filename):
    """Serve downloaded songs."""
    return send_from_directory(SONG_DIRECTORY, filename)

def run_flask():
    """Run the Flask web server."""
    app.run(host='0.0.0.0', port=5001)

if __name__ == "__main__":
    # Start the Flask web server in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start listening for songs
    start_listening()

    # Keep the main thread alive
    while True:
        time.sleep(1)