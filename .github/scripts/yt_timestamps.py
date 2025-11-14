import os
import re
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import codecs

# Try to load from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, continue with environment variables only

# Get the API key from environment variable
API_KEY = os.environ.get('API_KEY')
PLAYLIST_ID = 'PLhjZEVDFQUHtzHkfv2WzNgyZTPOxeuBHI'

def parse_games_md(file_path):
    games = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for a line that contains 'Date and Time', 'Result', and 'Matchup'
    table_header_pattern = r'\|\s*Date and Time\s*\|\s*Result\s*\|\s*Matchup\s*\|'
    table_start_match = re.search(table_header_pattern, content, re.IGNORECASE)
    
    if not table_start_match:
        print("Could not find the table header in the markdown file.")
        return games

    table_start = table_start_match.start()
    table_end = content.find('###', table_start)  # Assuming the table ends at the next header
    if table_end == -1:
        table_end = len(content)  # If no header found, assume table goes to end of file
    
    table_content = content[table_start:table_end]
    lines = table_content.split('\n')
    
    for line in lines[2:]:  # Skip header and separator
        if line.strip() and not line.startswith('|---'):
            parts = [part.strip() for part in line.split('|') if part.strip()]
            if len(parts) >= 3:
                date_time_str = parts[0]
                # Check if the date is already linked
                if not date_time_str.startswith('['):
                    try:
                        date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
                        result = parts[1]
                        matchup = parts[2]
                        games.append((date_time, result, matchup))
                    except ValueError:
                        print(f"Skipping invalid date format: {date_time_str}")
    
    # Sort games by date, newest first
    games.sort(key=lambda x: x[0], reverse=True)
    
    print(f"Parsed {len(games)} unlinked games from the markdown file.")
    return games

def match_games_to_videos(games, videos):
    matched_games = []
    for video_title, video_link, video_description, video_date in videos:
        print(f"Processing video: {video_title}")
        print(f"  Video date: {video_date.date()}")

        # Try the original format first
        game_infos = re.findall(r'(\d{2}:\d{2}:\d{2})\s+(Win|Loss)\s+(.*)', video_description or '', re.IGNORECASE)
        
        # If no matches, try the chapter/game details format
        if not game_infos:
            # Look for chapter timestamps and game results
            # Updated pattern to be more flexible and capture all games
            description_lines = (video_description or '').split('\n')
            
            for i, line in enumerate(description_lines):
                # Look for game sections with timestamps
                game_match = re.search(r'Game\s+(\d+)\s+\((\d{1,2}:\d{2}:\d{2})\)', line, re.IGNORECASE)
                if game_match:
                    game_time = game_match.group(2)
                    
                    # Look for opponent and result in the next few lines
                    for j in range(i+1, min(i+6, len(description_lines))):
                        next_line = description_lines[j]
                        
                        # Look for opponent line
                        opponent_match = re.search(r'Opponent:\s+([^(]+)\(([^)]+)\)', next_line, re.IGNORECASE)
                        
                        # Look for result line  
                        result_match = re.search(r'Result:\s+(Win|Loss)', next_line, re.IGNORECASE)
                        
                        if opponent_match and result_match:
                            opponent_name = opponent_match.group(1).strip()
                            opponent_civ = opponent_match.group(2).strip()
                            result = result_match.group(1)
                            
                            # Convert to HH:MM:SS format if needed
                            time_parts = game_time.split(':')
                            if len(time_parts) == 3:
                                formatted_time = game_time
                            elif len(time_parts) == 2:
                                formatted_time = f"0:{game_time}"
                            else:
                                continue
                                
                            # Create match info from the parsed data
                            match_info = f"vs {opponent_civ} ({opponent_name})"
                            game_infos.append((formatted_time, result, match_info))
                            print(f"    Found game: {formatted_time} {result} {match_info}")
                            break
                        elif opponent_match or result_match:
                            # Found one but not both, keep looking in same section
                            opponent_info = opponent_match if opponent_match else None
                            result_info = result_match if result_match else None
                            
                            # Continue searching for the missing piece
                            for k in range(j+1, min(i+8, len(description_lines))):
                                additional_line = description_lines[k]
                                if not opponent_info:
                                    opponent_match = re.search(r'Opponent:\s+([^(]+)\(([^)]+)\)', additional_line, re.IGNORECASE)
                                    if opponent_match:
                                        opponent_info = opponent_match
                                if not result_info:
                                    result_match = re.search(r'Result:\s+(Win|Loss)', additional_line, re.IGNORECASE)
                                    if result_match:
                                        result_info = result_match
                                
                                if opponent_info and result_info:
                                    opponent_name = opponent_info.group(1).strip()
                                    opponent_civ = opponent_info.group(2).strip()
                                    result = result_info.group(1)
                                    
                                    # Convert to HH:MM:SS format if needed
                                    time_parts = game_time.split(':')
                                    if len(time_parts) == 3:
                                        formatted_time = game_time
                                    elif len(time_parts) == 2:
                                        formatted_time = f"0:{game_time}"
                                    else:
                                        continue
                                        
                                    # Create match info from the parsed data
                                    match_info = f"vs {opponent_civ} ({opponent_name})"
                                    game_infos.append((formatted_time, result, match_info))
                                    print(f"    Found game: {formatted_time} {result} {match_info}")
                                    break
        
        print(f"  Found {len(game_infos)} games in video description")
        
        for time_str, result, match_info in game_infos:
            print(f"    Processing game: {time_str} {result} {match_info}")
            
            # Normalize video matchup
            match_info_normalized = ''.join(match_info.lower().split())
            result = result.strip().upper()
            
            game_time = datetime.strptime(time_str, '%H:%M:%S').time()
            game_datetime = datetime.combine(video_date.date(), game_time)
            
            if game_time.hour < 5:
                game_datetime += timedelta(days=1)
            
            for game_date, game_result, game_matchup in games:
                date_match = abs((game_date.date() - game_datetime.date()).days) <= 2
                result_match = game_result.strip().upper() == result
                # Normalize game matchup
                game_matchup_normalized = ''.join(game_matchup.lower().split())
                matchup_match = match_info_normalized in game_matchup_normalized
                
                if matchup_match:
                    print(f"    Partial match found:")
                    print(f"      Date match: {date_match} (Video: {game_datetime.date()}, Game: {game_date.date()})")
                    print(f"      Result match: {result_match} (Video: {result}, Game: {game_result.strip().upper()})")
                    print(f"      Matchup match: {matchup_match}")
                    print(f"      Video matchup (normalized): {match_info_normalized}")
                    print(f"      Game matchup (normalized): {game_matchup_normalized}")
                
                if date_match and result_match and matchup_match:
                    matched_game = (game_date.strftime('%Y-%m-%d %H:%M'), f"{video_link}&t={int(game_time.hour*3600 + game_time.minute*60 + game_time.second)}")
                    matched_games.append(matched_game)
                    print(f"    Full match found: {matched_game[0]}")
                    break
            else:
                print(f"    No match found for this game")

    print(f"Matched {len(matched_games)} games to videos.")
    return matched_games

def update_markdown_with_links(markdown_content, matched_games):
    if not matched_games:
        print("No games were matched. The markdown content will not be updated.")
        return markdown_content

    lines = markdown_content.split('\n')
    table_start = next((i for i, line in enumerate(lines) if '| Date and Time | Result | Matchup |' in line), -1)
    
    if table_start == -1:
        print("Could not find the table header in the markdown content. The content will not be updated.")
        return markdown_content

    for i in range(table_start + 2, len(lines)):
        line = lines[i]
        if line.strip() and not line.startswith('|---'):
            parts = [part.strip() for part in line.split('|')]
            if len(parts) >= 2:
                date_time = parts[1]
                # Only update if the date is not already a hyperlink
                if not date_time.startswith('['):
                    for game_date, timestamp in matched_games:
                        if game_date == date_time:
                            parts[1] = f'[{date_time}]({timestamp})'
                            lines[i] = '| ' + ' | '.join(parts[1:]) + ' |'
                            break

    return '\n'.join(lines)

def read_file_with_fallback_encoding(file_path, preferred_encoding='utf-8'):
    encodings_to_try = [preferred_encoding, 'utf-8-sig', 'utf-16', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings_to_try:
        try:
            with codecs.open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    raise ValueError(f"Unable to read the file {file_path} with any of the attempted encodings.")

def fetch_youtube_videos(api_key, playlist_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    videos = []
    next_page_token = None
    
    while True:
        try:
            playlist_items = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()

            for item in playlist_items.get('items', []):
                snippet = item['snippet']
                video_id = snippet['resourceId']['videoId']
                video_title = snippet['title']
                video_description = snippet['description']
                video_date = datetime.strptime(snippet['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                
                video_link = f'https://www.youtube.com/watch?v={video_id}'
                videos.append((video_title, video_link, video_description, video_date))

            next_page_token = playlist_items.get('nextPageToken')
            if not next_page_token:
                break

        except HttpError as e:
            print(f'An HTTP error {e.resp.status} occurred:\n{e.content}')
            break

    return videos

def main():
    if not API_KEY:
        raise ValueError("API_KEY environment variable is not set.")
    
    games = parse_games_md('content/games.md')
    videos = fetch_youtube_videos(API_KEY, PLAYLIST_ID)
    matched_games = match_games_to_videos(games, videos)

    # Read the current content of games.md using the new function
    markdown_content = read_file_with_fallback_encoding('content/games.md')

    # Update the markdown content with hyperlinks
    updated_markdown = update_markdown_with_links(markdown_content, matched_games)

    # Write the updated content back to games.md
    with codecs.open('content/games.md', 'w', encoding='utf-8') as f:
        f.write(updated_markdown)

    print("Updated games.md with hyperlinks.")

if __name__ == "__main__":
    main()
