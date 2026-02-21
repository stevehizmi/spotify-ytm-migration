"""Migrate Spotify saved tracks to YouTube Music playlist"""

import argparse
import json
import os
import re
import time
from datetime import datetime

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic, OAuthCredentials

# Load environment variables
load_dotenv()

# Get credentials from environment variables
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
YT_CLIENT_ID = os.getenv("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise ValueError(
        "Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables. "
        "See README.md for setup instructions."
    )

# Debug: Print credential status (first 10 chars only for security)
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    print("✓ Spotify credentials loaded")
else:
    print("✗ Warning: Spotify credentials not fully loaded")

scope = "user-library-read"

# Create Spotify OAuth manager with explicit cache file
cache_file = ".spotify_cache"
auth_manager = SpotifyOAuth(
    scope=scope,
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri="http://127.0.0.1:8000/callback",
    cache_path=cache_file,
)

sp = spotipy.Spotify(auth_manager=auth_manager)


def normalize_text(text):
    """Remove special characters and normalize for comparison"""
    if not text:
        return ""
    return re.sub(r"[^\w\s]", "", text.lower().strip())


def find_best_match(ytmusic, song_name, artist_name, threshold=0.7):
    """
    Search for a song and find the best matching result.
    Returns (videoId, matched_title, matched_artists) if good match found, (None, None, None) otherwise.
    """
    # Build better search query
    search_query = f"{song_name} {artist_name}"
    search_results = ytmusic.search(search_query, filter="songs", limit=5)

    if not search_results:
        return None, None, None

    # Normalize search terms for comparison
    normalized_song = normalize_text(song_name)
    normalized_artist = normalize_text(artist_name)

    # Score each result
    best_match = None
    best_score = 0

    for result in search_results:
        if "videoId" not in result:
            continue

        # Get result details
        result_title = normalize_text(result.get("title", ""))
        result_artists = [
            normalize_text(a.get("name", "")) for a in result.get("artists", [])
        ]

        # Calculate match score
        score = 0

        # Title match (most important)
        if normalized_song in result_title or result_title in normalized_song:
            score += 0.6
        # Partial title match
        elif any(
            word in result_title for word in normalized_song.split() if len(word) > 3
        ):
            score += 0.3

        # Artist match
        artist_matched = False
        for result_artist in result_artists:
            if normalized_artist in result_artist or result_artist in normalized_artist:
                score += 0.4
                artist_matched = True
                break
            # Partial artist match
            elif any(
                word in result_artist
                for word in normalized_artist.split()
                if len(word) > 3
            ):
                score += 0.2
                artist_matched = True
                break

        # Prefer official music videos/audio
        if result.get("resultType") == "song":
            score += 0.1

        if score > best_score:
            best_score = score
            best_match = result

    # Only return if score meets threshold
    if best_score >= threshold and best_match:
        return (
            best_match.get("videoId"),
            best_match.get("title", ""),
            best_match.get("artists", []),
        )

    return None, None, None


def add_song_to_playlist(ytmusic, song_name, artist_name, playlist_id):
    """Improved version with better matching"""
    video_id, matched_title, matched_artists = find_best_match(
        ytmusic, song_name, artist_name
    )

    if not video_id:
        return False, f"No good match found for: {song_name} by {artist_name}"

    try:
        ytmusic.add_playlist_items(playlist_id, [video_id], duplicates=False)
        matched_artist_str = (
            ", ".join([a.get("name", "") for a in matched_artists])
            if matched_artists
            else "Unknown"
        )
        return (
            True,
            f"Added: {song_name} by {artist_name} → Matched: {matched_title} by {matched_artist_str}",
        )
    except Exception as e:
        if "duplicate" in str(e).lower():
            return False, f"Duplicate: {song_name} by {artist_name}"
        else:
            return False, f"Error adding {song_name}: {e}"


def clear_playlist(ytmusic, playlist_id):
    """Clear all items from a playlist"""
    try:
        # Get all items in the playlist
        playlist_data = ytmusic.get_playlist(playlist_id, limit=None)
        tracks = playlist_data.get("tracks", [])

        # Extract video IDs - ytmusicapi uses 'videoId' or 'setVideoId'
        video_ids = []
        for item in tracks:
            video_id = item.get("videoId") or item.get("setVideoId")
            if video_id:
                video_ids.append(video_id)

        if video_ids:
            # Remove all items in batches if needed (API might have limits)
            # ytmusicapi remove_playlist_items can handle multiple items
            ytmusic.remove_playlist_items(playlist_id, video_ids)
            print(f"Cleared {len(video_ids)} items from playlist.")
        else:
            print("Playlist is already empty.")
        return True
    except Exception as e:
        print(f"Error clearing playlist: {e}")
        return False


def create_or_get_playlist(ytmusic, playlist_name, overwrite_existing=False):
    """
    Create or get existing playlist.
    If playlist exists and overwrite_existing is True, clears the playlist.
    If playlist exists and overwrite_existing is False, prompts user for action.
    Returns (playlist_id, is_new_playlist)
    """
    playlists = ytmusic.get_library_playlists()
    existing_playlist = next(
        (pl for pl in playlists if pl["title"] == playlist_name), None
    )

    if existing_playlist:
        playlist_id = existing_playlist["playlistId"]

        if overwrite_existing is None:
            # Prompt user for action
            print(f"\n⚠️  Playlist '{playlist_name}' already exists!")
            while True:
                choice = (
                    input(
                        "Would you like to (a)ppend to existing playlist or (o)verwrite it? [a/o]: "
                    )
                    .strip()
                    .lower()
                )
                if choice in ["a", "append"]:
                    print(f"Will append to existing playlist '{playlist_name}'.")
                    return playlist_id, False
                elif choice in ["o", "overwrite"]:
                    if clear_playlist(ytmusic, playlist_id):
                        print(
                            f"Playlist '{playlist_name}' cleared. Ready to add new tracks."
                        )
                        return playlist_id, False
                    else:
                        print("Failed to clear playlist. Exiting.")
                        return None, False
                else:
                    print("Please enter 'a' for append or 'o' for overwrite.")
        elif overwrite_existing:
            # Overwrite mode - clear the playlist
            if clear_playlist(ytmusic, playlist_id):
                print(f"Playlist '{playlist_name}' cleared. Ready to add new tracks.")
                return playlist_id, False
            else:
                print("Failed to clear playlist. Exiting.")
                return None, False
        else:
            # Append mode
            print(f"Playlist '{playlist_name}' already exists. Will append to it.")
            return playlist_id, False
    else:
        # Create new playlist
        new_playlist_id = ytmusic.create_playlist(
            playlist_name, "Created using ytmusicapi"
        )
        print(
            f"Playlist '{playlist_name}' created successfully. Playlist ID: {new_playlist_id}"
        )
        return new_playlist_id, True


def process_tracks(items, tracks_list):
    """Collect tracks as list of tuples: (song_name, artist_name, album_name)"""
    for item in items:
        track = item["track"]
        if track:  # Some tracks might be None
            # Join all artists if multiple
            if track["artists"]:
                if len(track["artists"]) > 1:
                    artist_name = ", ".join([a["name"] for a in track["artists"]])
                else:
                    artist_name = track["artists"][0]["name"]
            else:
                artist_name = "Unknown"

            song_name = track["name"]
            album_name = track["album"]["name"] if track.get("album") else ""
            tracks_list.append((song_name, artist_name, album_name))


# Main execution
def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Migrate Spotify saved tracks to YouTube Music playlist",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python spotify_collect.py
  python spotify_collect.py --playlist "My Spotify Favorites"
  python spotify_collect.py -p "My Playlist" --overwrite
        """,
    )
    parser.add_argument(
        "-p",
        "--playlist",
        type=str,
        default="test-spotify",
        help="Name of the YouTube Music playlist to create or use (default: test-spotify)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="If playlist exists, overwrite it without prompting (clears existing songs)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="If playlist exists, append to it without prompting",
    )

    args = parser.parse_args()

    # Determine overwrite behavior
    overwrite_existing = None
    if args.overwrite and args.append:
        print("Error: Cannot use both --overwrite and --append. Choose one.")
        return
    elif args.overwrite:
        overwrite_existing = True
    elif args.append:
        overwrite_existing = False

    print("Fetching tracks from Spotify...")
    tracks = []
    results = sp.current_user_saved_tracks(limit=50)
    process_tracks(results["items"], tracks)

    while results["next"]:
        results = sp.next(results)
        process_tracks(results["items"], tracks)

    print(f"Found {len(tracks)} tracks from Spotify\n")

    yt = YTMusic(
        "oauth.json",
        oauth_credentials=OAuthCredentials(
            client_id=YT_CLIENT_ID,
            client_secret=YT_CLIENT_SECRET,
        )
    )
    playlist_id, is_new = create_or_get_playlist(yt, args.playlist, overwrite_existing)

    if playlist_id is None:
        print("Failed to get or create playlist. Exiting.")
        return

    successful = 0
    failed = 0
    failed_tracks = []

    print("\nStarting to add tracks to YouTube Music...\n")

    for song_name, artist_name, album_name in tracks:
        success, message = add_song_to_playlist(yt, song_name, artist_name, playlist_id)
        print(message)

        if success:
            successful += 1
        else:
            failed += 1
            failed_tracks.append(
                {
                    "song": song_name,
                    "artist": artist_name,
                    "album": album_name,
                    "reason": message,
                }
            )

        time.sleep(1)  # Rate limiting

    print(f"\n{'='*60}")
    print(f"✅ Successfully added: {successful}")
    print(f"❌ Failed to add: {failed}")
    print(f"{'='*60}")

    # Save failed tracks to a file for manual review
    if failed_tracks:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        failed_file = f"failed_tracks_{timestamp}.json"
        with open(failed_file, "w", encoding="utf-8") as f:
            json.dump(failed_tracks, f, indent=2)
        print(f"\nFailed tracks saved to: {failed_file}")

if __name__ == "__main__":
    main()
