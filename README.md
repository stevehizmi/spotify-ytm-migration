# Spotify to YouTube Music Migration Tool

A Python tool to migrate your Spotify liked songs to a YouTube Music playlist, with intelligent song matching.

## Features

- **Smart Matching**: Scoring algorithm finds the best match on YouTube Music (title + artist)
- **Progress Tracking**: Real-time progress and a summary at the end
- **Duplicate Prevention**: Automatically skips songs already in the playlist
- **Failed Track Log**: Saves unmatched songs to a JSON file for manual review
- **Flexible Playlist Options**: Create a new playlist, append to an existing one, or overwrite it

## Prerequisites

- Python 3.10 or higher
- A [Spotify Developer](https://developer.spotify.com/dashboard) account
- A [Google Cloud](https://console.cloud.google.com) account (for YouTube Music API)
- A YouTube Music account

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/spotify-ytm-migration.git
cd spotify-ytm-migration
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Spotify API Credentials

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click **Create App**
3. Fill in a name and description, then under **Redirect URIs** add:
   ```
   http://127.0.0.1:8000/callback
   ```
4. Save and copy your **Client ID** and **Client Secret**

### 4. YouTube Music OAuth Credentials

YouTube Music requires OAuth credentials from Google Cloud:

1. Go to the [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or select an existing one)
3. Enable the **YouTube Data API v3**:
   - In the left sidebar go to **APIs & Services → Library**
   - Search for "YouTube Data API v3" and click **Enable**
4. Create OAuth credentials:
   - Go to **APIs & Services → Credentials**
   - Click **Create Credentials → OAuth client ID**
   - Choose **Desktop app** as the application type
   - Copy your **Client ID** and **Client Secret**
5. Run the YouTube Music authentication:
   ```bash
   ytmusicapi oauth --client-id YOUR_YT_CLIENT_ID --client-secret YOUR_YT_CLIENT_SECRET
   ```
   Follow the browser prompts to log in to your Google/YouTube Music account. This creates an `oauth.json` file.

### 5. Configure Environment Variables

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in all four credentials:
   ```
   SPOTIFY_CLIENT_ID=your_spotify_client_id_here
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
   YT_CLIENT_ID=your_youtube_client_id_here
   YT_CLIENT_SECRET=your_youtube_client_secret_here
   ```

---

## Usage

### Basic — migrate to a playlist named "My Spotify Songs"

```bash
python spotify_collect.py --playlist "My Spotify Songs"
```

On first run, a browser window will open asking you to authorize the Spotify connection.

### Options

| Flag | Description |
|------|-------------|
| `-p` / `--playlist` | Playlist name to create or use (default: `test-spotify`) |
| `--append` | If the playlist exists, add songs without removing existing ones |
| `--overwrite` | If the playlist exists, clear it first then add songs |

If the playlist already exists and you don't pass `--append` or `--overwrite`, the script will ask what you'd like to do.

### Examples

```bash
# Use default playlist name "test-spotify"
python spotify_collect.py

# Custom playlist name
python spotify_collect.py --playlist "Spotify Likes"

# Always append, never prompt
python spotify_collect.py --playlist "Spotify Likes" --append

# Clear the playlist and start fresh
python spotify_collect.py --playlist "Spotify Likes" --overwrite
```

---

## How It Works

Each Spotify track is searched on YouTube Music. The tool scores each result:

- **Title match** — 60% weight (exact or partial)
- **Artist match** — 40% weight (exact or partial)
- **Result type** — slight bonus for official songs

A score of **0.7 or higher** is required to add the song. Tracks below the threshold are saved to a `failed_tracks_YYYYMMDD_HHMMSS.json` file for manual review.

---

## Troubleshooting

**"No good match found" for many songs**
Some songs may not exist on YouTube Music, or have different titles/artist names. Check the `failed_tracks_*.json` file and add them manually.

**Spotify authentication fails**
Make sure the redirect URI in your Spotify app settings exactly matches: `http://127.0.0.1:8000/callback`

**YouTube Music token expires**
Re-run the auth command:
```bash
ytmusicapi oauth --client-id YOUR_YT_CLIENT_ID --client-secret YOUR_YT_CLIENT_SECRET
```

**Rate limiting**
The script waits 1 second between requests. If you hit rate limits, edit `spotify_collect.py` and change:
```python
time.sleep(1)  # increase to 2 or 3 if needed
```

---

## Security Notes

- Never commit `.env` or `oauth.json` — they're in `.gitignore`
- Keep your credentials private and don't share them

---

## File Structure

```
spotify-ytm-migration/
├── spotify_collect.py    # Main migration script
├── youtube_collect.py    # Standalone YouTube Music test script
├── requirements.txt      # Python dependencies
├── .env.example          # Template for environment variables
├── .gitignore
└── README.md
```

---

## License

MIT License — contributions welcome via Pull Request.

## Acknowledgments

- [spotipy](https://github.com/spotipy-dev/spotipy) — Spotify Web API wrapper
- [ytmusicapi](https://github.com/sigma67/ytmusicapi) — YouTube Music API wrapper
