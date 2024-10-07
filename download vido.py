import pytube
import pytube.exceptions
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import time
import re

DOWNLOAD_HISTORY_FILE = "download_history.txt"

def save_to_history(video_url, title):
    with open(DOWNLOAD_HISTORY_FILE, "a") as file:
        file.write(f"{title}: {video_url}\n")

def load_download_history():
    if os.path.exists(DOWNLOAD_HISTORY_FILE):
        with open(DOWNLOAD_HISTORY_FILE, "r") as file:
            return file.readlines()
    return []

def validate_url(url):
    pattern = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})$'
    return re.match(pattern, url) is not None

def preview_video():
    url = entry_url.get().strip()
    if validate_url(url):
        try:
            yt = pytube.YouTube(url)
            title = yt.title
            length = yt.length
            status_label.config(text=f"Preview: {title} | Duration: {length // 60}m {length % 60}s")
        except Exception as e:
            status_label.config(text=f"Error retrieving video details: {str(e)}")
    else:
        status_label.config(text="Invalid YouTube URL.")

def download_video():
    url = entry_url.get().strip()
    save_path = save_path_var.get()
    file_format = format_combobox.get()

    if not url or not save_path:
        status_label.config(text="Please provide both URL and save path")
        return

    if not validate_url(url):
        status_label.config(text="Invalid YouTube URL. Please check the format.")
        return

    threading.Thread(target=download_thread, args=(url, save_path, file_format), daemon=True).start()

def download_thread(url, save_path, file_format):
    global start_time
    start_time = time.time()
    try:
        yt = pytube.YouTube(url)
        title = yt.title
        status_label.config(text=f"Selected: {title}")

        if file_format == "MP4":
            stream = yt.streams.get_highest_resolution()
        elif file_format == "MP3":
            stream = yt.streams.filter(only_audio=True).first()
        else:
            status_label.config(text="Select a valid format")
            return

        print(f"Selected stream: {stream}")
        
        progress_bar['maximum'] = stream.filesize
        progress_bar['value'] = 0
        status_label.config(text=f"Downloading {title}...")

        stream.download(output_path=save_path, on_progress_callback=progress_callback)

        status_label.config(text="Download Complete")
        save_to_history(url, title)
        messagebox.showinfo("Download Complete", f"Downloaded: {title}")

    except pytube.exceptions.RegexMatchError:
        status_label.config(text="Invalid YouTube URL. Please check the URL format.")
    except pytube.exceptions.VideoUnavailable:
        status_label.config(text="The video is unavailable.")
    except pytube.exceptions.ExtractError:
        status_label.config(text="Download failed. Check your internet connection or format.")
    except Exception as e:
        status_label.config(text=f"Error: {str(e)}")
        print(f"Unexpected error: {e}")

def progress_callback(stream, chunk, bytes_remaining):
    bytes_downloaded = stream.filesize - bytes_remaining
    progress_bar['value'] = bytes_downloaded

    time_elapsed = time.time() - start_time
    if time_elapsed > 0:
        speed = bytes_downloaded / time_elapsed
        time_remaining = bytes_remaining / speed if speed > 0 else 0
        progress_label.config(text=f"Downloaded: {bytes_downloaded} of {stream.filesize} bytes. Estimated time remaining: {int(time_remaining)} seconds.")
    else:
        progress_label.config(text="Starting download...")

    root.update_idletasks()

def browse_save_path():
    save_path_var.set(filedialog.askdirectory())

def download_playlist():
    url = entry_url.get().strip()
    save_path = save_path_var.get()

    if not url or not save_path:
        status_label.config(text="Please provide both URL and save path")
        return

    if not validate_url(url):
        status_label.config(text="Invalid YouTube playlist URL.")
        return

    try:
        playlist = pytube.Playlist(url)
        status_label.config(text=f"Downloading playlist: {playlist.title}")
        
        for video_url in playlist.video_urls:
            download_thread(video_url, save_path, format_combobox.get())

    except Exception as e:
        status_label.config(text=f"Error downloading playlist: {str(e)}")
        print(f"Unexpected error: {e}")

root = tk.Tk()
root.title("YouTube Downloader")
root.geometry("700x500")

url_label = tk.Label(root, text="Enter the YouTube URL or Playlist URL:")
url_label.pack(pady=5)
entry_url = tk.Entry(root, width=50)
entry_url.pack(pady=5)

save_path_label = tk.Label(root, text="Save to:")
save_path_label.pack(pady=5)
save_path_var = tk.StringVar()
save_path_entry = tk.Entry(root, textvariable=save_path_var, width=40)
save_path_entry.pack(pady=5)
browse_btn = tk.Button(root, text="Browse", command=browse_save_path)
browse_btn.pack(pady=5)

format_label = tk.Label(root, text="Select the file format:")
format_label.pack(pady=5)
format_combobox = ttk.Combobox(root, values=["MP3", "MP4"], state="readonly")
format_combobox.pack(pady=5)


preview_btn = tk.Button(root, text="Preview Video", command=preview_video)
preview_btn.pack(pady=5)

download_btn = tk.Button(root, text="Download Video", command=download_video)
download_btn.pack(pady=20)

playlist_btn = tk.Button(root, text="Download Playlist", command=download_playlist)
playlist_btn.pack(pady=5)

progress_bar = ttk.Progressbar(root, length=300, mode='determinate')
progress_bar.pack(pady=10)

progress_label = tk.Label(root, text="")
progress_label.pack(pady=5)

status_label = tk.Label(root, text="")
status_label.pack(pady=5)

download_history = load_download_history()
if download_history:
    print("Download History:")
    for line in download_history:
        print(line.strip())

root.mainloop()
