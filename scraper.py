import requests
from bs4 import BeautifulSoup
import json
import re
import time
import os
from urllib.parse import urlparse, parse_qs
import yt_dlp

def get_video_source_from_vixcloud(embed_url):
    try:
        print(f"\nAttempting to extract video source from: {embed_url}")
        
        # Send a GET request to the embed URL
        response = requests.get(embed_url)
        if response.status_code != 200:
            print(f"Failed to fetch embed page. Status code: {response.status_code}")
            return None
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug: Print all script contents
        print("\nSearching for video source in scripts...")
        
        # First try to find the downloadUrl in the scripts
        for script in soup.find_all('script'):
            if script.string and 'window.downloadUrl' in script.string:
                print("Found downloadUrl in script!")
                match = re.search(r"window\.downloadUrl\s*=\s*['\"](.*?)['\"]", script.string)
                if match:
                    video_source = match.group(1)
                    print(f"Found video source: {video_source}")
                    return video_source
        
        # If downloadUrl not found, try to find sources array
        for script in soup.find_all('script'):
            if script.string and 'sources' in script.string:
                print("Found sources in script!")
                # Try different patterns to extract the video source
                patterns = [
                    r'sources:\s*\[\s*{\s*file:\s*["\'](.*?)["\']',  # Original pattern
                    r'file:\s*["\'](.*?)["\']',  # Simpler pattern
                    r'src:\s*["\'](.*?)["\']',   # Alternative pattern
                    r'url:\s*["\'](.*?)["\']'    # Another alternative
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, script.string)
                    if match:
                        video_source = match.group(1)
                        print(f"Found video source with pattern '{pattern}': {video_source}")
                        return video_source
        
        print("\nNo video source found in any script")
        return None
        
    except Exception as e:
        print(f"Error getting video source: {str(e)}")
        import traceback
        print("Full error traceback:")
        print(traceback.format_exc())
        return None

def download_episode(episode_info, output_dir='downloads'):
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get the video source from VixCloud
        video_source = get_video_source_from_vixcloud(episode_info['embed_url'])
        if not video_source:
            print(f"Could not get video source for episode {episode_info['number']}")
            print("Trying alternative method...")
            
            # Try to get the video source from the direct link
            if episode_info.get('url'):
                print(f"Using direct link: {episode_info['url']}")
                video_source = episode_info['url']
            else:
                print("No alternative source available")
                return False
        
        # Validate the video source URL
        if not video_source.startswith(('http://', 'https://')):
            print(f"Invalid video source URL: {video_source}")
            return False
        
        # Create filename from episode info
        filename = f"Episode_{episode_info['number']}_{episode_info['title']}.%(ext)s"
        # Remove any invalid characters from filename
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filepath = os.path.join(output_dir, filename)
        
        print(f"\nDownloading episode {episode_info['number']}...")
        print(f"Source: {video_source}")
        print(f"Destination: {filepath}")
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best',  # Download best quality
            'outtmpl': filepath,  # Output template
            'quiet': False,  # Show progress
            'no_warnings': False,  # Show warnings
            'progress_hooks': [lambda d: print(f"\rProgress: {d['_percent_str']} of {d['_total_bytes_str']} at {d['_speed_str']}", end='') if d['status'] == 'downloading' else None],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': episode_info['embed_url']
            }
        }
        
        # Download using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([video_source])
                print(f"\nDownload completed: {filename}")
                return True
            except yt_dlp.utils.DownloadError as e:
                print(f"\nDownload failed: {str(e)}")
                if "not a valid URL" in str(e):
                    print("The video source URL appears to be invalid. Please check the URL format.")
                return False
        
    except Exception as e:
        print(f"Error downloading episode: {str(e)}")
        import traceback
        print("Full error traceback:")
        print(traceback.format_exc())
        return False

def scrape_episode_by_id(url, episode_id):
    # Construct the episode URL
    url = f"{url}/{episode_id}"
    
    # Send a GET request to the URL
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch the episode. Status code: {response.status_code}")
        return None
    
    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the video-player component
    video_player = soup.select_one('video-player')
    if not video_player:
        print("Video player component not found")
        return None
        
    # Extract the episode data
    episode_data = video_player.get('episode')
    if not episode_data:
        print("No episode data found")
        return None
    
    try:
        # Parse the episode JSON data
        episode = json.loads(episode_data)        
        # Format the episode data
        episode_info = {
            'id': episode.get('id'),
            'number': episode.get('number'),
            'title': episode.get('file_name', '').replace('Mushoku.Tensei.Jobless.Reincarnation.S02E', '').replace('.1080p.CR.WEB-DL.JPN.AAC2.0.H.264.mkv', ''),
            'url': episode.get('link'),
            'views': episode.get('visite'),
            'date': episode.get('created_at'),
            'embed_url': video_player.get('embed_url'),
            'anime_id': episode.get('anime_id')
        }
        
        return episode_info
    except json.JSONDecodeError as e:
        print(f"Error parsing episode data: {e}")
        return None

def scrape_anime_episodes(url):
    # Send a GET request to the URL
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch the page. Status code: {response.status_code}")
        return None
    
    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the video-player component
    video_player = soup.select_one('video-player')
    if not video_player:
        print("Video player component not found")
        return None
    
    # Extract the episodes data from the episodes attribute
    episodes_data = video_player.get('episodes')
    if not episodes_data:
        print("No episodes data found")
        return None
    
    try:
        # Parse the episodes JSON data
        episodes = json.loads(episodes_data)
        
        # Format the episode data
        formatted_episodes = []
        for episode in episodes:
            episode_info = {
                'id': episode.get('id'),
                'number': episode.get('number'),
                'title': episode.get('file_name', '').replace('Mushoku.Tensei.Jobless.Reincarnation.S02E', '').replace('.1080p.CR.WEB-DL.JPN.AAC2.0.H.264.mkv', ''),
                'url': episode.get('link'),
                'views': episode.get('visite'),
                'date': episode.get('created_at')
            }
            formatted_episodes.append(episode_info)
        
        return formatted_episodes
    except json.JSONDecodeError as e:
        print(f"Error parsing episodes data: {e}")
        return None

def save_episodes_to_json(episodes, filename='episodes.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(episodes, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(episodes)} episodes to {filename}")

# Example usage
if __name__ == "__main__":
    # Get anime URL from user input
    anime_url = input("Please enter the anime URL (e.g., https://www.animeunity.so/anime/1469-naruto): ").strip()
    
    # Validate URL
    if not anime_url.startswith("https://www.animeunity.so/anime/"):
        print("Invalid URL format. URL should start with 'https://www.animeunity.so/anime/'")
        exit(1)
    
    # First, get all episodes
    episodes = scrape_anime_episodes(anime_url)
    
    if episodes:
        print(f"\nFound {len(episodes)} episodes. Scraping details for each episode...\n")
        
        # Scrape details for each episode
        all_episode_details = []
        for episode in episodes:
            print(f"\nScraping episode {episode['number']} (ID: {episode['id']})...")
            episode_details = scrape_episode_by_id(anime_url, episode['id'])
            
            if episode_details:
                all_episode_details.append(episode_details)
                print(f"Episode {episode['number']} details:")
                print(json.dumps(episode_details, indent=4))
                print("-" * 80)
                
                # Download the episode
                download_episode(episode_details)
            else:
                print(f"Failed to scrape details for episode {episode['number']}")
            
            # Add a small delay to avoid overwhelming the server
            time.sleep(1)
        
        # Save all episode details to a JSON file
        if all_episode_details:
            save_episodes_to_json(all_episode_details, 'episode_details.json')
            print("\nAll episode details have been saved to 'episode_details.json'")
    else:
        print("No episodes were found or an error occurred.")
