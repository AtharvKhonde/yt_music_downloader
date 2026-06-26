
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


# 🎵 YouTube Music Downloader

A Python-based batch audio downloader for YouTube and YouTube Music that converts videos to high-quality MP3 format. Built with `yt-dlp` and designed for both single-track and bulk downloads.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Core Functions](#core-functions)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)
- [License](#license)

---

## 🎯 Overview

This project provides a robust Python script to download audio from YouTube and YouTube Music URLs. It handles URL normalization, format conversion, batch processing, and error recovery. The script is optimized for both **local execution** (recommended) and Google Colab (with limitations).

### Why This Exists

YouTube Music and YouTube do not provide a native bulk download feature. This tool bridges that gap by leveraging `yt-dlp` — the most actively maintained YouTube downloader — to extract audio streams and convert them to MP3.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Batch Processing** | Download hundreds of songs in one run |
| **URL Normalization** | Auto-converts `music.youtube.com` to standard YouTube URLs |
| **Smart Search** | Accepts song names (searches YouTube) or direct URLs |
| **MP3 Conversion** | Extracts audio and converts to 192kbps MP3 via FFmpeg |
| **Error Isolation** | One failed download doesn't stop the entire batch |
| **Rate Limiting** | Configurable delays between downloads to avoid blocks |
| **Progress Tracking** | Real-time status: `[5/311] ✅ Done: 'Song Title.mp3'` |
| **Cookie Support** | Optional authentication via browser cookies |

---

## 📦 Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.8+ | Script runtime |
| **yt-dlp** | Latest | YouTube extraction engine |
| **FFmpeg** | 4.0+ | Audio extraction & MP3 conversion |

### Optional (for restricted videos)

| Tool | Purpose |
|------|---------|
| **Browser cookies** | Bypass "Sign in to confirm you're not a bot" |
| **Node.js** | JavaScript challenge solving (yt-dlp advanced) |

### Platform-Specific Installation

#### macOS (Recommended)

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install yt-dlp ffmpeg node

# Verify installations
yt-dlp --version    # Should print version number
ffmpeg -version     # Should print version info
node --version      # Should print v18+ or v20+
```

#### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt-get update

# Install FFmpeg and Node.js
sudo apt-get install -y ffmpeg nodejs npm

# Install yt-dlp via pip
pip install -U yt-dlp

# Verify
yt-dlp --version
ffmpeg -version
```

#### Windows

1. Download **FFmpeg** from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
2. Download **yt-dlp** from [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases) and add to PATH
3. Download **Node.js** from [nodejs.org](https://nodejs.org/) and install

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/youtube-music-downloader.git
cd youtube-music-downloader
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**`requirements.txt`:**
```
yt-dlp>=2024.12.0
```

---

## 🗂️ Project Structure

```
youtube-music-downloader/
├── download_music.py      # Main script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── cookies.txt           # Optional: YouTube auth cookies
└── downloads/            # Default output folder
    └── musicdown/
        ├── Song Title 1.mp3
        ├── Song Title 2.mp3
        └── ...
```

---

## 🔧 Core Functions

### `normalize_youtube_url(text)`

**Purpose:** Detects and normalizes YouTube URLs, including `music.youtube.com` links.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | `str` | Raw input string (URL or search query) |

**Returns:** `tuple(bool, str)` — `(is_url: bool, processed_url: str)`

**Behavior:**
- Matches URLs from `youtube.com`, `youtu.be`, `music.youtube.com`, `youtube-nocookie.com`
- Extracts the 11-character video ID using regex
- Converts `music.youtube.com` URLs to `www.youtube.com` format for better compatibility
- Returns `(False, original_text)` for non-URL inputs (treated as search queries)

**Regex Pattern:**
```python
r'(https?://)?(www\.)?(music\.youtube|youtube|youtu|youtube-nocookie)\.(com|be)/'
r'(watch\?v=|embed/|v/|.+
```

**Example:**
```python
>>> normalize_youtube_url("https://music.youtube.com/watch?v=abc123xyz789")
(True, "https://www.youtube.com/watch?v=abc123xyz789")

>>> normalize_youtube_url("The Weeknd Blinding Lights")
(False, "The Weeknd Blinding Lights")
```

---

### `download_audio(query, index, total)`

**Purpose:** Downloads a single song by name or URL, converts to MP3, and saves to disk.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | Song name or YouTube URL |
| `index` | `int` | Current position in batch (for progress display) |
| `total` | `int` | Total number of songs (for progress display) |

**Returns:** `str | None` — Full file path if successful, `None` if failed

**Internal Flow:**
1. **Normalize URL** — Calls `normalize_youtube_url()` to process input
2. **Configure yt-dlp** — Sets format, output path, postprocessors
3. **Search or Direct Download** — Prepends `ytsearch1:` for song names
4. **Extract & Download** — Uses `yt_dlp.YoutubeDL.extract_info()` with `download=True`
5. **Find Saved File** — Scans output folder for the new `.mp3` file
6. **Return Path** — Returns absolute path for batch tracking

**yt-dlp Options Used:**
| Option | Value | Purpose |
|--------|-------|---------|
| `format` | `bestaudio/best` | Select highest quality audio stream |
| `outtmpl` | `%(title)s.%(ext)s` | Filename template using video metadata |
| `postprocessors` | `FFmpegExtractAudio` | Converts downloaded audio to MP3 |
| `preferredcodec` | `mp3` | Target audio format |
| `preferredquality` | `192` | MP3 bitrate in kbps |
| `geo_bypass` | `True` | Bypass geographic restrictions |
| `nocheckcertificate` | `True` | Skip SSL certificate verification |
| `retries` | `3` | Retry failed network requests |
| `fragment_retries` | `3` | Retry failed video fragment downloads |

**Error Handling:**
- Catches all exceptions, prints truncated error message
- Returns `None` so the batch loop continues with next song
- Never crashes the entire batch on a single failure

---

### Main Execution Loop

**Purpose:** Iterates through the `SONGS` list, calls `download_audio()` for each, tracks results.

**Features:**
- Skips empty strings
- Implements `time.sleep(DELAY_BETWEEN_SONGS)` between downloads
- Counts successes and failures
- Prints final summary report

---

## ⚙️ Configuration

### Song List (`SONGS`)

Edit the `SONGS` list in `download_music.py`:

```python
SONGS = [
    # Direct YouTube URLs
    "https://www.youtube.com/watch?v=4NRXx6U8ABQ",
    "https://music.youtube.com/watch?v=znvky0Uq8qc",

    # Search queries (yt-dlp will find best match)
    "The Weeknd Blinding Lights",
    "Ed Sheeran Shape of You",
    "lofi hip hop radio",

    # Artist + Song combinations work best
    "Adele Someone Like You",
]
```

### Output Folder (`OUTPUT_FOLDER`)

```python
# macOS
OUTPUT_FOLDER = "/Users/atharvkhonde/Downloads/musicdown"

# Linux
OUTPUT_FOLDER = "/home/username/Music"

# Windows
OUTPUT_FOLDER = "C:\\Users\\Username\\Downloads\\Music"
```

### Rate Limiting (`DELAY_BETWEEN_SONGS`)

```python
DELAY_BETWEEN_SONGS = 3  # Seconds between downloads
```

- **Small batches (<50):** `0-2` seconds
- **Medium batches (50-150):** `2-5` seconds
- **Large batches (150+):** `5-10` seconds

### Cookies (`COOKIES_PATH`)

For age-restricted or bot-flagged videos:

1. Install browser extension: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckphmjdalfnhikbalaldpd)
2. Go to `youtube.com` and ensure you're logged in
3. Click extension → Export → Save as `cookies.txt`
4. Place in project folder and set:

```python
COOKIES_PATH = "/Users/atharvkhonde/Downloads/cookies.txt"
```

---

## ▶️ Usage

### Basic Usage

```bash
python download_music.py
```

### Expected Output

```
📁 Download folder: /Users/atharvkhonde/Downloads/musicdown
🎵 Total songs: 5
============================================================

[1/5] 📥 Downloading: https://www.youtube.com/watch?v=4NRXx6U8ABQ
   ✅ Done: 'Blinding Lights.mp3'

[2/5] 🔍 Searching: 'The Weeknd Blinding Lights'
   ✅ Done: 'The Weeknd - Blinding Lights (Official Video).mp3'

[3/5] 🔍 Searching: 'Ed Sheeran Shape of You'
   ✅ Done: 'Ed Sheeran - Shape of You (Official Music Video).mp3'

...

============================================================
📊 Results: 5 succeeded, 0 failed
💾 Files saved to: /Users/atharvkhonde/Downloads/musicdown
============================================================
```

### Running in Background (Large Batches)

```bash
# Run detached from terminal, logs to file
nohup python download_music.py > download_log.txt 2>&1 &

# Check progress
tail -f download_log.txt
```

---

## 🐛 Troubleshooting

### "Sign in to confirm you're not a bot"

| Cause | Solution |
|-------|----------|
| IP flagged by YouTube | Use cookies (see Configuration section) |
| Google Colab IP blocked | **Run locally on your Mac instead** |
| Too many rapid requests | Increase `DELAY_BETWEEN_SONGS` |

### "Requested format is not available"

| Cause | Solution |
|-------|----------|
| Video is private/deleted | Remove from `SONGS` list |
| Region-blocked video | Enable VPN or skip song |
| YouTube Music DRM | Use regular `youtube.com` URL instead |

### "FFmpeg not found"

```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg

# Verify
ffmpeg -version
```

### "yt-dlp not found"

```bash
pip install -U yt-dlp
```

### Slow Downloads

- Check your internet speed
- YouTube throttles some IP ranges
- Try different DNS (Cloudflare `1.1.1.1` or Google `8.8.8.8`)

---

## ⚠️ Limitations

### Platform Limitations

| Platform | Status | Notes |
|----------|--------|-------|
| **Local Mac/Linux/Windows** | ✅ Fully Supported | Recommended for all use cases |
| **Google Colab** | ❌ Not Recommended | YouTube blocks Colab IPs; 311 songs will fail |
| **GitHub Codespaces** | ❌ Not Supported | Similar IP blocking issues |

### YouTube Restrictions

- **Age-restricted videos:** Require cookies or account login
- **Private videos:** Cannot be downloaded
- **Livestreams:** Only downloadable after stream ends
- **YouTube Premium exclusives:** May require subscription cookies

### Rate Limits

- YouTube enforces unknown rate limits per IP
- Large batches (300+) should use delays of 5-10 seconds
- Consider splitting into multiple sessions over several hours

---

## 📚 Dependencies

### Core Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| `yt-dlp` | `>=2024.12.0` | YouTube video/audio extraction |
| `ffmpeg` | `>=4.0` | Audio codec conversion to MP3 |

### Python Standard Library

| Module | Usage |
|--------|-------|
| `re` | URL validation and video ID extraction |
| `os` | Directory creation and file path handling |
| `sys` | Python executable path for dependency checks |
| `time` | Rate limiting delays between downloads |

---

## 🔒 Legal & Ethical Notice

This tool is intended for **personal use only**. Respect copyright laws and YouTube's Terms of Service:

- ✅ Downloading your own content
- ✅ Downloading Creative Commons licensed content
- ✅ Personal offline listening (fair use, varies by jurisdiction)
- ❌ Redistribution of copyrighted material
- ❌ Commercial use of downloaded content
- ❌ Circumventing DRM protections

**The authors are not responsible for misuse of this tool.**

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — The engine behind this tool
- [FFmpeg](https://ffmpeg.org/) — Audio processing powerhouse
- YouTube creators — Support them by streaming officially when possible

---

**Happy downloading! 🎧**
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
