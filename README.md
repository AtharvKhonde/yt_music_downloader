
# 🎵 YouTube Music Playlist URL Extractor

A Google Colab-ready Python toolkit to extract all individual song URLs from public YouTube Music playlists. Handles large playlists (1000+ songs) reliably using two extraction methods.

---

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Libraries Used](#libraries-used)
- [Architecture & Functions](#architecture--functions)
- [Usage](#usage)
  - [Method A: yt-dlp (Quick, No API Key)](#method-a-yt-dlp)
  - [Method B: YouTube Data API v3 (Bulletproof)](#method-b-youtube-data-api-v3)
- [Common Issues & Solutions](#common-issues--solutions)
- [Output Files](#output-files)
- [FAQ](#faq)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Dual Methods** | `yt-dlp` for quick extraction, YouTube Data API for 100% reliability |
| **Large Playlist Support** | Handles playlists with 1000+ songs via API pagination |
| **Bot Detection Bypass** | API method avoids YouTube's bot checks entirely |
| **Multiple Outputs** | Exports to `.txt`, `.csv`, and `.json` |
| **Colab Optimized** | One-click file downloads after extraction |
| **No Downloads** | Only extracts metadata — never downloads audio/video |

---

## 🔧 Prerequisites

### For Method A (yt-dlp)
| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.8+ | Colab runs 3.10+ by default |
| `yt-dlp` | Latest nightly | `pip install --upgrade yt-dlp` |
| Internet | — | YouTube blocks some datacenter IPs |

### For Method B (YouTube Data API)
| Requirement | How to Get |
|-------------|------------|
| Google Account | [signup](https://accounts.google.com) |
| Google Cloud Project | [console](https://console.cloud.google.com/) |
| YouTube Data API v3 Key | Enable API → Credentials → API Key |
| API Quota | 10,000 units/day (free tier) |

> **Quota Math**: Fetching 50 playlist items = **1 unit**. A 1,000-song playlist costs only **20 units**.

---

## 📦 Installation

```bash
# Method A dependency
pip install --upgrade yt-dlp

# Method B dependency
pip install google-api-python-client
```

**In Google Colab**, run this in a cell:
```python
!pip install -q --upgrade yt-dlp google-api-python-client
```

---

## 📚 Libraries Used

| Library | Purpose | Method |
|---------|---------|--------|
| **`yt-dlp`** | Extracts playlist metadata by scraping YouTube's internal APIs | A |
| **`google-api-python-client`** | Official Google SDK for YouTube Data API v3 | B |
| **`re`** (built-in) | Regex to parse `list=` parameter from any YouTube URL | B |
| **`json`** (built-in) | Serializes song data to structured `.json` files | Both |
| **`csv`** (built-in) | Exports tabular data to `.csv` for spreadsheets | Both |
| **`google.colab.files`** | Triggers browser download of output files in Colab | Both |

---

## 🏗️ Architecture & Functions

### Method A: `yt_dlp` Extraction

```python
def extract_with_ytdlp(playlist_url: str) -> list[dict]:
    """
    Uses yt-dlp's extract_flat mode to scrape playlist metadata.
    
    Args:
        playlist_url: Full YouTube Music playlist URL
    
    Returns:
        List of dicts: {index, title, url, duration, video_id}
    
    Known Limitations:
        - YouTube pagination bug caps extraction at ~100-120 items
          on some playlists (active yt-dlp issue as of 2026)
        - May trigger bot detection on datacenter IPs (e.g. Colab)
    """
```

| `yt_dlp` Option | Purpose |
|-----------------|---------|
| `extract_flat='in_playlist'` | Only fetch metadata, skip full video extraction |
| `skip_download=True` | Never download media files |
| `extractor_args={'youtubetab': {'skip': 'webpage'}}` | **Workaround**: Uses API instead of webpage parsing to bypass 100-item limit |
| `playlistend=None` | Request all items (theoretical; bug may still limit) |

---

### Method B: YouTube Data API v3

```python
def extract_playlist_id(url: str) -> str:
    """
    Parses any YouTube/YT Music URL to extract the playlist ID.
    
    Supports:
        - https://music.youtube.com/playlist?list=PL...
        - https://youtube.com/playlist?list=PL...
        - https://www.youtube.com/watch?v=...&list=PL...
    
    Returns:
        Raw playlist ID string (e.g., 'PLxxxxxxxxxxxxxxxxxxx')
    """

def fetch_all_songs(api_key: str, playlist_id: str) -> list[dict]:
    """
    Paginates through YouTube Data API to retrieve EVERY song.
    
    YouTube API returns max 50 items per request. This function
    automatically follows nextPageToken until all pages are consumed.
    
    Args:
        api_key: Your YouTube Data API v3 key
        playlist_id: Extracted playlist ID
    
    Returns:
        Complete list of all songs with index, title, video_id, url
    """
```

| API Parameter | Purpose |
|---------------|---------|
| `part='snippet,contentDetails'` | Fetches title (snippet) and video ID (contentDetails) |
| `maxResults=50` | API hard limit per request |
| `pageToken` | Pagination cursor — empty on first call, then `nextPageToken` from previous response |

---

### Shared Utilities

```python
def save_outputs(songs: list[dict]) -> None:
    """
    Generates three output formats simultaneously:
    
    1. playlist_urls.txt      → One URL per line (for import into other tools)
    2. playlist_songs.csv     → Spreadsheet with columns: index, title, video_id, url
    3. playlist_songs.json     → Structured data with full metadata
    
    All files are UTF-8 encoded to support international characters.
    """

def download_from_colab() -> None:
    """
    Uses google.colab.files to trigger browser download.
    Only works in Google Colab environment.
    """
```

---

## 🚀 Usage

### Method A: yt-dlp (No API Key Required)

```python
import yt_dlp

PLAYLIST_URL = "https://music.youtube.com/playlist?list=YOUR_PLAYLIST_ID"

ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'extract_flat': 'in_playlist',
    'extractor_args': {
        'youtubetab': {'skip': 'webpage'}
    },
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(PLAYLIST_URL, download=False)
    entries = info.get('entries', [])
    
    songs = []
    for idx, entry in enumerate(entries, 1):
        vid = entry['id']
        songs.append({
            'index': idx,
            'title': entry.get('title', 'Unknown'),
            'url': f"https://music.youtube.com/watch?v={vid}",
            'video_id': vid,
        })
```

**When to use**: Small playlists (<100 songs), quick one-off extractions.

---

### Method B: YouTube Data API v3 (Recommended)

```python
from googleapiclient.discovery import build
import re

API_KEY = "YOUR_API_KEY_HERE"
PLAYLIST_URL = "https://music.youtube.com/playlist?list=YOUR_PLAYLIST_ID"

# Extract playlist ID
playlist_id = re.search(r'[?&]list=([a-zA-Z0-9_-]+)', PLAYLIST_URL).group(1)

youtube = build('youtube', 'v3', developerKey=API_KEY)

songs = []
next_page_token = None

while True:
    request = youtube.playlistItems().list(
        part='snippet,contentDetails',
        playlistId=playlist_id,
        maxResults=50,
        pageToken=next_page_token
    )
    response = request.execute()
    
    for item in response['items']:
        vid = item['contentDetails']['videoId']
        songs.append({
            'index': item['snippet']['position'] + 1,
            'title': item['snippet']['title'],
            'video_id': vid,
            'url': f"https://music.youtube.com/watch?v={vid}",
        })
    
    next_page_token = response.get('nextPageToken')
    if not next_page_token:
        break

print(f"Extracted {len(songs)} songs")
```

**When to use**: Large playlists, production scripts, scheduled/automated runs.

---

## ⚠️ Common Issues & Solutions

### 1. "Only 106 songs extracted" (Pagination Bug)

| Symptom | yt-dlp stops at ~100-120 items despite playlist having 500+ |
|---------|-------------------------------------------------------------|
| **Cause** | Active yt-dlp bug with YouTube's continuation token handling |
| **Fix** | Use **Method B (YouTube Data API)** — it paginates correctly via `nextPageToken` |
| **Workaround** | Add `extractor_args={'youtubetab': {'skip': 'webpage'}}` — may bump limit to ~230 |

### 2. "Sign in to confirm you're not a bot"

| Symptom | `ERROR: Sign in to confirm you're not a bot` |
|---------|----------------------------------------------|
| **Cause** | YouTube detects Colab/datacenter IP and requires JS challenge solving |
| **Fix** | Use **Method B (YouTube Data API)** — official API never triggers bot checks |
| **Alternative** | Pass cookies: `--cookies-from-browser chrome` (requires local machine, not Colab) |

### 3. "No supported JavaScript runtime found"

| Symptom | `WARNING: No supported JavaScript runtime could be found` |
|---------|-----------------------------------------------------------|
| **Cause** | yt-dlp needs a JS engine to solve YouTube's player challenges |
| **Fix** | In Colab: `!pip install -q deno-bin` or switch to **Method B** |

### 4. Playlist is "Unlisted" or Private

| Symptom | `No entries found` or empty result |
|---------|-----------------------------------|
| **Cause** | Both methods require the playlist to be **Public** |
| **Fix** | Go to YouTube Studio → Playlist settings → Visibility → **Public** |

---

## 📁 Output Files

After running either method, three files are generated:

| File | Format | Use Case |
|------|--------|----------|
| `playlist_urls.txt` | One URL per line | Import into download managers, share URL lists |
| `playlist_songs.csv` | Spreadsheet | Open in Excel/Google Sheets for sorting/filtering |
| `playlist_songs.json` | Structured JSON | Programmatic processing, backup, API responses |

**Sample JSON output:**
```json
[
  {
    "index": 1,
    "title": "Song Title",
    "video_id": "znvky0Uq8qc",
    "url": "https://music.youtube.com/watch?v=znvky0Uq8qc"
  }
]
```

---

## ❓ FAQ

**Q: Do I need a YouTube Music subscription?**
> No. Public playlists are accessible to anyone.

**Q: Can I extract from regular YouTube playlists too?**
> Yes. Both methods work for `youtube.com/playlist?list=...` and `music.youtube.com/playlist?list=...`.

**Q: Is this legal?**
> Yes. This only extracts **publicly available metadata** (titles and URLs). No audio/video is downloaded.

**Q: Why does the API method need a key but yt-dlp doesn't?**
> yt-dlp reverse-engineers YouTube's internal (unofficial) APIs. The Data API is official and requires authentication.

**Q: Can I run this locally instead of Colab?**
> Absolutely. Remove the `google.colab.files` download lines and files will save to your local directory.

---

## 📜 License

MIT — Free for personal and commercial use.

---

**Pro Tip**: For playlists larger than 200 songs, skip the troubleshooting and go straight to **Method B**. The 5 minutes spent getting an API key saves hours of debugging yt-dlp pagination issues.

Python script using yt-dlp (the best maintained YouTube downloader). It accepts either a song name or a direct YouTube link, then downloads the audio as an MP3.


Optional: Add Metadata & Thumbnails
If you have ffmpeg installed, you can enhance the script to embed thumbnail art:
Python

```python
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [
        {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        },
        {
            'key': 'EmbedThumbnail',  # Embeds cover art
        },
        {
            'key': 'FFmpegMetadata',  # Adds title/artist metadata
        },
    ],
    'writethumbnail': True,
    'outtmpl': '%(title)s.%(ext)s',
}
```
Note: ffmpeg must be installed on your system for audio conversion and metadata embedding. Download it from ffmpeg.org if needed.

Note: Make sure ffmpeg is installed for audio conversion to MP3. If not, the script will download the audio but may fail to convert it. You can install it via apt-get install ffmpeg (Linux) or download from ffmpeg.org.

The files are saved to your current working directory — in Jupyter, that's typically the same folder where your notebook file (.ipynb) is located.
If you want to save to a specific folder (e.g., /home/user/Music), add this to the ydl_opts:
```python
output_folder = "/home/user/Music"  # Change to your preferred path
ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),  # <-- saves here
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}
```
It downloads audio only, then converts it to MP3.
Here's the proof from the code:
```python
'format': 'bestaudio/best',           # <-- picks best audio stream only
'postprocessors': [{
    'key': 'FFmpegExtractAudio',      # <-- extracts audio using ffmpeg
    'preferredcodec': 'mp3',          # <-- converts to MP3
    'preferredquality': '192',        # <-- 192 kbps quality
}],
```

⚠️ Important Note on ffmpeg
The conversion to MP3 requires ffmpeg installed on your system. If ffmpeg is missing:
yt-dlp will still download the audio but likely in a format like .webm or .m4a
It won't convert to .mp3
Check if you have ffmpeg:
```Python
!ffmpeg -version
```
If missing, install it:
Linux: apt-get install ffmpeg
Mac: brew install ffmpeg


| Feature                | Implementation                                              |
| ---------------------- | ----------------------------------------------------------- |
| **Output location**    | `OUTPUT_FOLDER = "/Users/atharvkhonde/Downloads/musicdown"` |
| **Auto-create folder** | `os.makedirs(OUTPUT_FOLDER, exist_ok=True)`                 |
| **Audio-only**         | `'format': 'bestaudio/best'`                                |
| **MP3 conversion**     | `FFmpegExtractAudio` postprocessor                          |
| **File path**          | `os.path.join(OUTPUT_FOLDER, '%(title)s.%(ext)s')`          |


How It Works in Colab
| Step | What Happens                                                                       |
| ---- | ---------------------------------------------------------------------------------- |
| 1    | Downloads MP3s to Colab's cloud storage (`/content/musicdown`)                     |
| 2    | After all downloads finish, sends each file to your browser                        |
| 3    | Files appear in your **browser's default download folder** (usually `~/Downloads`) |
