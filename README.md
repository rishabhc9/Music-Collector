# Music Collector
## Features:
1. Song Identification:
    * Uses the Shazam API to identify songs playing around you.
    * Records audio snippets and matches them against Shazam’s database.
2. Song History Tracking:
    * Keeps a detailed history of all identified songs, including:
        * Song title and artist
        * Date and time of recognition
        * Time category (morning, afternoon, evening, night)
        * Day of the week
3. Song Downloading:
    * Automatically downloads identified songs using yt-dlp.
    * Organizes downloaded songs into a dedicated folder.
4. Listening Trends Chart (Desktop App)
    * Top Songs Chart (A chart that displays the total listening duration for each song & visualizes the top 20 songs based on listening duration.)
    * Top Artists Chart (A chart that displays the number of unique songs identified for each artist & Visualizes the top 20 artists based on the number of unique songs identified)
5. Filtering, Sorting & Searching (only for Desktop app)
    * Allows users to filter the song history based on specific parameters (Title, Artist, Date, Time, Day of Week, Time Category).
    * Allows users to sort the song history in ascending or descending order based on a selected parameter.
    * Allows user to search for a specific song
6. Listening Trends Dashboard (Web Interface):
    * A Flask-based web dashboard to visualize your listening habits:
        * Unique songs and artists
        * Most active day of the week
        * Songs You've Listened to by Artist 
        * Daily Count of Fresh Tracks
        * Your Music Hotspots Throughout the Month (Time Slot when you discover the most tracks)

## Installation & Setup  

### Clone the Repository  
```sh
git clone https://github.com/rishabhc9/Music-Collector.git
cd Music-Collector
```
### Run the program (Desktop App with GUI)
```sh
python3 MusicCollector.py
```
### Run the program (Desktop App with auto-downloading)
```sh
python3 autoscript.py
```
### Run the program (Web Interface, cd inside rpi_music_collector folder and run)
```sh
python3 autoscript_for_rpi.py
```
### Make Sure to install these libraries
```sh
yt-dlp==2025.1.26
ytmdl==2024.8.15.1
httpx==0.27.2
shazamio==0.6.0
```
>>> 
## Desktop Interface
<img width="994" alt="Screenshot 2025-02-27 at 10 14 28 PM" src="https://github.com/user-attachments/assets/cc461318-62b4-42c8-8a89-088a21d9c18a" />
<img width="994" alt="Screenshot 2025-02-28 at 12 18 45 AM" src="https://github.com/user-attachments/assets/46903000-b3b6-4b00-b5b1-7a08a40dee78" />
<img width="994" alt="Screenshot 2025-02-28 at 12 19 18 AM" src="https://github.com/user-attachments/assets/a78e92e7-d18e-41b2-bea8-9aa6c495b1df" />

## Web Interface (for rpi)

<img width="1679" alt="Screenshot 2025-02-28 at 12 42 44 AM" src="https://github.com/user-attachments/assets/a7fd4f8e-0d24-458b-aab5-b93b8c054921" />
<img width="1680" alt="Screenshot 2025-02-28 at 12 39 32 AM" src="https://github.com/user-attachments/assets/6f62fa0d-274e-4757-8e12-e34aa7cde59c" />
<img width="1680" alt="Screenshot 2025-02-28 at 12 39 58 AM" src="https://github.com/user-attachments/assets/5f4d8abc-2dbb-4ed8-b76c-268445bc0c1d" />
<img width="1680" alt="Screenshot 2025-02-28 at 12 40 18 AM" src="https://github.com/user-attachments/assets/4daa3a7f-05b3-4b3b-af66-825a2c335ed6" />
