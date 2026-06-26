!pip install -q google-api-python-client

from googleapiclient.discovery import build
import re

# --- CONFIG ---
API_KEY = ""  # Paste your YouTube Data API key
PLAYLIST_URL = "https://music.youtube.com/playlist?list=PLDAdaT0myIgNKdJdG27fR5uIlWXfQN3Zd&si=Elwy4rPjbPBVqIVH"

# Extract playlist ID from any YouTube/YT Music URL
def extract_playlist_id(url):
    match = re.search(r'[?&]list=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    raise ValueError("Could not find playlist ID in URL")

PLAYLIST_ID = extract_playlist_id(PLAYLIST_URL)

# --- FETCH ALL SONGS ---
youtube = build('youtube', 'v3', developerKey=API_KEY)

songs = []
next_page_token = None
page = 1

print(f"Fetching playlist: {PLAYLIST_ID}\n")

while True:
    request = youtube.playlistItems().list(
        part='snippet,contentDetails',
        playlistId=PLAYLIST_ID,
        maxResults=50,  # API max per request
        pageToken=next_page_token
    )
    response = request.execute()

    items = response.get('items', [])
    print(f"Page {page}: Got {len(items)} items")

    for item in items:
        video_id = item['contentDetails']['videoId']
        title = item['snippet']['title']
        position = item['snippet']['position'] + 1  # 1-based

        # YouTube Music URL
        song_url = f"https://music.youtube.com/watch?v={video_id}"

        songs.append({
            'index': position,
            'title': title,
            'video_id': video_id,
            'url': song_url
        })

    next_page_token = response.get('nextPageToken')
    if not next_page_token:
        break
    page += 1

# --- RESULTS ---
print(f"\n{'='*60}")
print(f"✅ TOTAL SONGS EXTRACTED: {len(songs)}")
print(f"{'='*60}\n")

for song in songs[:10]:  # Print first 10
    print(f"{song['index']}. {song['title']}")
    print(f"   {song['url']}")

if len(songs) > 10:
    print(f"\n... and {len(songs) - 10} more")

# --- SAVE FILES ---
import json, csv

# Text file (URLs only)
with open('playlist_urls.txt', 'w') as f:
    for s in songs:
        f.write(s['url'] + '\n')

# CSV
with open('playlist_songs.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['index', 'title', 'video_id', 'url'])
    writer.writeheader()
    writer.writerows(songs)

# JSON
with open('playlist_songs.json', 'w', encoding='utf-8') as f:
    json.dump(songs, f, indent=2, ensure_ascii=False)

# Download to your computer
from google.colab import files
files.download('playlist_urls.txt')
files.download('playlist_songs.csv')
files.download('playlist_songs.json')

print("\n📥 Files downloaded: playlist_urls.txt, playlist_songs.csv, playlist_songs.json")
