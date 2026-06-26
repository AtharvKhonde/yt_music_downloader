# ============================================================
# INSTALL DEPENDENCIES
# ============================================================

import subprocess
subprocess.run(["pip", "install", "-q", "google-api-python-client"], check=True)
subprocess.run(["pip", "install", "-q", "yt_dlp"], check=True)

import re
import os
import time
import json
import csv
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from googleapiclient.discovery import build
from google.colab import files

try:
    import yt_dlp
except ImportError:
    subprocess.run(["pip", "install", "-q", "yt_dlp"])
    import yt_dlp

# ============================================================
# CONFIGURATION  ← only section you need to edit
# ============================================================

API_KEY      = "YOUR_YOUTUBE_API_KEY"   # Paste your YouTube Data API key here
PLAYLIST_URL = "https://music.youtube.com/playlist?list=PLDAdaT0myIgNKdJdG27fR5uIlWXfQN3Zd"

OUTPUT_FOLDER = "/content/musicdown"
MAX_WORKERS   = 4    # Parallel downloads (keep 3–5 to avoid rate limiting)
MAX_RETRIES   = 3    # Retry attempts per song on failure

SAVE_PLAYLIST_FILES = True   # Set False to skip saving txt/csv/json to disk

# ============================================================
# STEP 1 — EXTRACT PLAYLIST ID
# ============================================================

def extract_playlist_id(url):
    match = re.search(r'[?&]list=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not find playlist ID in URL: {url}")

PLAYLIST_ID = extract_playlist_id(PLAYLIST_URL)
print(f"📋 Playlist ID : {PLAYLIST_ID}")

# ============================================================
# STEP 2 — FETCH ALL SONGS VIA YOUTUBE DATA API
# ============================================================

print(f"\n🔍 Fetching playlist songs from YouTube API...")

youtube    = build('youtube', 'v3', developerKey=API_KEY)
songs      = []
next_token = None
page       = 1

while True:
    request  = youtube.playlistItems().list(
        part        = 'snippet,contentDetails',
        playlistId  = PLAYLIST_ID,
        maxResults  = 50,
        pageToken   = next_token
    )
    response = request.execute()
    items    = response.get('items', [])
    print(f"   Page {page}: {len(items)} items fetched")

    for item in items:
        video_id = item['contentDetails']['videoId']
        title    = item['snippet']['title']
        position = item['snippet']['position'] + 1  # 1-based index

        # Skip deleted/private videos that YouTube returns as placeholders
        if title in ("Deleted video", "Private video"):
            print(f"   ⚠️  Skipping {title} at position {position}")
            continue

        songs.append({
            'index'    : position,
            'title'    : title,
            'video_id' : video_id,
            'url'      : f"https://music.youtube.com/watch?v={video_id}"
        })

    next_token = response.get('nextPageToken')
    if not next_token:
        break
    page += 1

print(f"\n{'='*60}")
print(f"✅ Total songs found : {len(songs)}")
print(f"{'='*60}")
print("\nFirst 10 songs:")
for s in songs[:10]:
    print(f"   {s['index']:>3}. {s['title']}")
    print(f"        {s['url']}")
if len(songs) > 10:
    print(f"\n   ... and {len(songs) - 10} more")

# ============================================================
# STEP 3 — OPTIONALLY SAVE PLAYLIST FILES
# ============================================================

if SAVE_PLAYLIST_FILES:
    with open('playlist_urls.txt', 'w') as f:
        for s in songs:
            f.write(s['url'] + '\n')

    with open('playlist_songs.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['index', 'title', 'video_id', 'url'])
        writer.writeheader()
        writer.writerows(songs)

    with open('playlist_songs.json', 'w', encoding='utf-8') as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)

    print("\n💾 Saved: playlist_urls.txt, playlist_songs.csv, playlist_songs.json")

# ============================================================
# STEP 4 — SETUP DOWNLOAD FOLDER
# ============================================================

if os.path.exists(OUTPUT_FOLDER):
    shutil.rmtree(OUTPUT_FOLDER)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

SONG_URLS = [s['url'] for s in songs]

print(f"\n📁 Output folder : {OUTPUT_FOLDER}")
print(f"🎵 Total songs   : {len(SONG_URLS)}")
print(f"⚡ Workers       : {MAX_WORKERS}")
print("=" * 60)

# ============================================================
# STEP 5 — DOWNLOAD
# ============================================================

def is_youtube_url(text):
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?(music\.)?youtube\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return bool(youtube_regex.match(text))


def download_audio(query, index, total):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(OUTPUT_FOLDER, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    if not is_youtube_url(query):
        safe_print(f"[{index}/{total}] 🔍 Searching: '{query}'")
        query = f"ytsearch1:{query}"
    else:
        safe_print(f"[{index}/{total}] 📥 URL: {query}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            title = (
                info['entries'][0]['title']
                if 'entries' in info and info['entries']
                else info.get('title', 'Unknown')
            )
        safe_print(f"[{index}/{total}] ✅ Done: '{title}'")
        return True

    except Exception as e:
        safe_print(f"[{index}/{total}] ❌ Error: {e}")
        return False


def download_with_retry(query, index, total):
    for attempt in range(1, MAX_RETRIES + 1):
        if download_audio(query, index, total):
            return True
        if attempt < MAX_RETRIES:
            wait = 2 ** attempt
            safe_print(f"[{index}/{total}] 🔄 Retry {attempt}/{MAX_RETRIES - 1} in {wait}s...")
            time.sleep(wait)
    safe_print(f"[{index}/{total}] 💀 Giving up after {MAX_RETRIES} attempts.")
    return False


success_count = 0
fail_count    = 0
failed_urls   = []

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {
        executor.submit(download_with_retry, url, i, len(SONG_URLS)): url
        for i, url in enumerate(SONG_URLS, 1)
    }
    for future in as_completed(futures):
        if future.result():
            success_count += 1
        else:
            failed_urls.append(futures[future])
            fail_count += 1

files_on_disk = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.mp3')]

print("\n" + "=" * 60)
print("📊 DOWNLOAD SUMMARY")
print(f"   Songs in playlist : {len(SONG_URLS)}")
print(f"   ✅ Succeeded      : {success_count}")
print(f"   ❌ Failed         : {fail_count}")
print(f"   📂 Files on disk  : {len(files_on_disk)}")
if failed_urls:
    print("\n   Failed URLs:")
    for url in failed_urls:
        print(f"      {url}")
print("=" * 60)

# ============================================================
# STEP 6 — ZIP FOLDER AND SEND TO YOUR MAC
# ============================================================

if files_on_disk:
    print(f"\n📦 Zipping {len(files_on_disk)} file(s)...")
    shutil.make_archive("/content/musicdown", 'zip', OUTPUT_FOLDER)

    zip_size_mb = os.path.getsize("/content/musicdown.zip") / (1024 * 1024)
    print(f"   Zip size : {zip_size_mb:.1f} MB")
    print("⬇️  Sending zip to your computer...")
    files.download("/content/musicdown.zip")
    print("✅ Done! Check your browser's downloads folder.")
else:
    print("\n⚠️  No files to download.")
