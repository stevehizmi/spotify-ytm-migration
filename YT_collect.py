from ytmusicapi import YTMusic
import re

def normalize_text(text):
    """Remove special characters and normalize for comparison"""
    if not text:
        return ""
    return re.sub(r'[^\w\s]', '', text.lower().strip())

def create_or_get_playlist(ytmusic, playlist_name):
    """Create or get existing playlist"""
    playlists = ytmusic.get_library_playlists()
    existing_playlist = next((pl for pl in playlists if pl['title'] == playlist_name), None)
    
    if existing_playlist:
        print(f"Playlist '{playlist_name}' already exists. Playlist ID: {existing_playlist['playlistId']}")
        return existing_playlist['playlistId']
    else:
        new_playlist_id = ytmusic.create_playlist(playlist_name, 'Created using ytmusicapi')
        print(f"Playlist '{playlist_name}' created successfully. Playlist ID: {new_playlist_id}")
        return new_playlist_id

yt = YTMusic('oauth.json')
playlist_id = create_or_get_playlist(yt, "test")

# Search for a specific song with filter
search_results = yt.search('Ride Twenty One Pilots', filter="songs", limit=5)

# Print the search results for debugging
print("Search Results:")
for i, result in enumerate(search_results):
    print(f"\nResult {i}:")
    print(f"  Title: {result.get('title', 'N/A')}")
    print(f"  Artists: {[a.get('name', '') for a in result.get('artists', [])]}")
    print(f"  Video ID: {result.get('videoId', 'N/A')}")
    print(f"  Result Type: {result.get('resultType', 'N/A')}")

# Check if there are any search results
if not search_results:
    print("\nNo search results found.")
else:
    # Use the first result (index 0) instead of index 1
    if "videoId" not in search_results[0]:
        print("\nNo videoId found in the first search result.")
    else:
        video_id = search_results[0]["videoId"]
        yt.add_playlist_items(playlist_id, [video_id])
        print(f"\n✅ Added song to playlist. Video ID: {video_id}")
        print(f"   Title: {search_results[0].get('title', 'N/A')}")
