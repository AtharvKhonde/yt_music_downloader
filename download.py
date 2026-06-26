import re
import os
import time
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.colab import files

try:
    import yt_dlp
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "-q", "yt_dlp"])
    import yt_dlp

# ============================================================
# CONFIGURATION
# ============================================================

PLAYLIST_FILE = "playlist_urls.txt"
OUTPUT_FOLDER = "/content/musicdown"
MAX_WORKERS   = 4    # Parallel downloads (keep 3–5 to avoid rate limiting)
MAX_RETRIES   = 3    # Retry attempts per song on failure

# ============================================================
# STEP 1 — UPLOAD YOUR playlist_urls.txt
# ============================================================

print("📂 Please upload your playlist_urls.txt file...")
uploaded = files.upload()

if PLAYLIST_FILE not in uploaded:
    PLAYLIST_FILE = list(uploaded.keys())[0]
    print(f"   (Using uploaded file: '{PLAYLIST_FILE}')")

raw_lines = uploaded[PLAYLIST_FILE].decode("utf-8").splitlines()
SONGS = [line.strip() for line in raw_lines if line.strip() and not line.strip().startswith("#")]

print(f"✅ Loaded {len(SONGS)} URLs from '{PLAYLIST_FILE}'")

# ============================================================
# SETUP
# ============================================================

if os.path.exists(OUTPUT_FOLDER):
    shutil.rmtree(OUTPUT_FOLDER)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

print(f"\n📁 Output folder : {OUTPUT_FOLDER}")
print(f"🎵 Total songs   : {len(SONGS)}")
print(f"⚡ Workers       : {MAX_WORKERS}")
print("=" * 60)

# ============================================================
# HELPERS
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

# ============================================================
# STEP 2 — PARALLEL DOWNLOAD
# ============================================================

success_count = 0
fail_count    = 0
failed_urls   = []

valid_songs = list(enumerate(SONGS, 1))

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {
        executor.submit(download_with_retry, song, i, len(valid_songs)): song
        for i, song in valid_songs
    }
    for future in as_completed(futures):
        if future.result():
            success_count += 1
        else:
            failed_urls.append(futures[future])
            fail_count += 1

# Count actual files on disk — ground truth
files_on_disk = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.mp3')]

print("\n" + "=" * 60)
print("📊 DOWNLOAD SUMMARY")
print(f"   Songs requested  : {len(SONGS)}")
print(f"   ✅ Succeeded     : {success_count}")
print(f"   ❌ Failed        : {fail_count}")
print(f"   📂 Files on disk : {len(files_on_disk)}")
if failed_urls:
    print("\n   Failed URLs:")
    for url in failed_urls:
        print(f"      {url}")
print("=" * 60)

# ============================================================
# STEP 3 — ZIP ENTIRE FOLDER AND SEND TO YOUR MAC
# ============================================================

if files_on_disk:
    print(f"\n📦 Zipping {len(files_on_disk)} file(s) from folder...")

    # Zips everything in OUTPUT_FOLDER directly — no tracking lists, no gaps
    shutil.make_archive("/content/musicdown", 'zip', OUTPUT_FOLDER)

    zip_size_mb = os.path.getsize("/content/musicdown.zip") / (1024 * 1024)
    print(f"   Zip size : {zip_size_mb:.1f} MB")
    print("⬇️  Sending zip to your computer...")
    files.download("/content/musicdown.zip")
    print("✅ Done! Check your browser's downloads folder.")
else:
    print("\n⚠️  No files to download.")
