# GameClips
A lightweight Windows desktop application that automatically detects your latest gameplay recordings and seamlessly uploads them to your Google Drive, saving local storage effortlessly.





# 🎮 Automatic Game Clip Upload to Google Drive

**Stop uploading your clips by hand.** This project watches the folder where your PC saves your best plays and uploads them to Google Drive on its own, the moment they finish recording. Turn on your PC, play, and your clips are already safe in the cloud — no extra work required.

---

## ✨ What it does

- 👀 Watches your clips folder in real time
- ⏳ Waits until the file is fully written (no corrupted uploads)
- ☁️ Automatically uploads it to the Drive folder you choose
- 🔁 Resumes automatically if the connection drops mid-upload
- 🚫 Never uploads the same clip twice

---

## 🚀 Getting started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up your Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project
3. Search for **"Google Drive API"** and click **Enable**
4. Go to **OAuth consent screen** → type **External** → add your email as a test user
5. Go to **Credentials → Create credentials → OAuth client ID** → type **Desktop app**
6. Download the JSON, rename it to `credentials.json`, and place it next to the script

### 3. Configure the script

Open `GameClips.py` and edit:

```python
CARPETA_CLIPS = r"C:\Users\YOUR_USER\Videos\NVIDIA\Highlights" or another directory
CARPETA_DRIVE_ID = "YOUR_DRIVE_FOLDER_ID_HERE"
```

### 4. Fire it up!

```bash
python subir_clips_drive.py
```

The first run opens your browser to authorize access. After that, everything runs automatically.

### 5. Make it start on its own

Set it up in **Windows Task Scheduler** to run at login, and forget it exists.

---

## 💰 Does it cost anything?

**No.** The Google Drive API is free for personal use, and the script runs on your own PC. The only thing you might eventually need is more Drive storage if you fill up the free 15 GB.

---

## ⚠️ Things to keep in mind

| Problem | How the script already handles it |
|---|---|
| Uploading a half-recorded clip | Waits until file size stabilizes |
| Connection drops | Resumable upload with automatic retry |
| Duplicate clips | Local database tracks what's already been uploaded |
| Filling up Drive | Keep an eye on storage and clear old clips now and then |

---

**Your best plays, safe, effortlessly.** 🏆
