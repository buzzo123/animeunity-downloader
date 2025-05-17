# Anime Unity Scraper

A Python script to scrape and download anime episodes from Anime Unity.

## Features

- Scrapes episode information from Anime Unity
- Downloads episodes in MP4 format
- Saves episode details to JSON file
- Supports all anime available on Anime Unity

## Requirements

- Python 3.x
- Required Python packages (see `requirements.txt`):
  - requests
  - beautifulsoup4
  - yt-dlp

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/animeunity_scraper.git
cd animeunity_scraper
```

2. Install the required packages using pip:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the script:
```bash
python scraper.py
```

2. When prompted, enter the Anime Unity URL of the anime you want to download. For example:
```
https://www.animeunity.so/anime/1469-naruto
```

3. The script will:
   - Scrape all available episodes
   - Download each episode to the `downloads` directory
   - Save episode details to `episode_details.json`

## Output

- Downloaded episodes will be saved in the `downloads` directory
- Episode information will be saved in `episode_details.json`
- Each episode will be named in the format: `Episode_[number]_[title].mp4`

## Notes

- The script includes a small delay between requests to avoid overwhelming the server
- Downloaded files are automatically ignored by Git (see `.gitignore`)
- Make sure you have sufficient disk space for the downloads
- The script requires an active internet connection

## Disclaimer

This tool is for educational purposes only. Please respect copyright laws and the terms of service of Anime Unity. Only download content that you have the right to access. 