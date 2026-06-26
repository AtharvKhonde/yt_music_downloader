# yt_music_downloader
This project help extract YouTube music link and then download locally.

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
