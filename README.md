# Spotify to YouTube Music Migration Tool

A Python tool to migrate your Spotify saved tracks (liked songs) to YouTube Music playlists with intelligent song matching.

## Features

- 🎵 **Smart Song Matching**: Uses a scoring algorithm to find the best matches on YouTube Music
- 🎯 **Accurate Results**: Filters search results to only include songs, avoiding videos and playlists
- 📊 **Progress Tracking**: Shows real-time progress and generates a report of unmatched songs
- 🔄 **Duplicate Prevention**: Automatically skips duplicate songs in playlists
- 📝 **Failed Track Logging**: Saves unmatched songs to a JSON file for manual review
- 🎨 **Multiple Artists Support**: Handles tracks with multiple artists correctly

## Prerequisites

- Python 3.7 or higher
- Spotify Developer Account (for API credentials)
- YouTube Music account

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

### 3. Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy your **Client ID** and **Client Secret**
4. Add `http://localhost/` as a redirect URI in your app settings

### 4. YouTube Music Authentication

1. Install `ytmusicapi` if not already installed: `pip install ytmusicapi`
2. Run the authentication command:
   ```bash
   ytmusicapi oauth
   ```
3. Follow the prompts to authenticate with your Google account
4. This will create an `oauth.json` file (already in `.gitignore`)

### 5. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Spotify credentials:
   ```
   SPOTIFY_CLIENT_ID=your_spotify_client_id_here
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
   ```

## Usage

### Basic Usage

Run the main script to migrate your Spotify saved tracks:

```bash
python spotify_collect.py
```

The script will:
1. Fetch all your saved tracks from Spotify
2. Create or find a playlist named "test-spotify" on YouTube Music
3. Search for each song on YouTube Music and add the best match
4. Display progress and generate a report

### Customizing the Playlist Name

Edit `spotify_collect.py` and change the playlist name:

```python
playlist_id = create_or_get_playlist(yt, "your-playlist-name")
```

## How It Works

### Matching Algorithm

The tool uses a scoring system to find the best matches:

- **Title Match** (60% weight): Checks if the song title matches
- **Artist Match** (40% weight): Verifies the artist matches
- **Partial Matches**: Handles variations and partial matches
- **Result Type**: Prefers official songs over other content types

Only songs with a match score ≥ 0.7 are added to ensure accuracy.

### Output

The script provides:
- Real-time progress updates showing each song being processed
- Success/failure counts at the end
- A JSON file (`failed_tracks_YYYYMMDD_HHMMSS.json`) containing all unmatched songs for manual review

## File Structure

```
spotify-ytm-migration/
├── spotify_collect.py    # Main migration script
├── YT_collect.py         # Testing/example script
├── requirements.txt      # Python dependencies
├── .env.example         # Example environment variables
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## Troubleshooting

### "No good match found" errors

Some songs may not be found on YouTube Music. These are saved to a JSON file for manual review. Common reasons:
- Song not available on YouTube Music
- Different title/artist name formatting
- Regional availability restrictions

### Authentication Issues

- **Spotify**: Make sure your redirect URI is set to `http://localhost/` in the Spotify Developer Dashboard
- **YouTube Music**: Re-run `ytmusicapi oauth` if your token expires

### Rate Limiting

The script includes a 1-second delay between requests to avoid rate limiting. If you encounter rate limit errors, increase the delay in `spotify_collect.py`:

```python
time.sleep(2)  # Increase from 1 to 2 seconds
```

## Security Notes

- Never commit your `.env` file or `oauth.json` to version control
- These files are already in `.gitignore` for your protection
- Keep your API credentials secure and don't share them

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Acknowledgments

- [spotipy](https://github.com/spotipy-dev/spotipy) - Spotify Web API wrapper
- [ytmusicapi](https://github.com/sigma67/ytmusicapi) - YouTube Music API wrapper
