import requests
import re
from datetime import datetime

API_URL = "https://aoe4world.com/api/v0/games?profile_ids=17272020"
GAMES_FILE = "content/games.md"
TITUS_PROFILE_ID = 17272020

def fetch_all_games_from_api():
    """Fetch all games from the API with pagination"""
    all_games = []
    page = 1
    
    while True:
        print(f"Fetching page {page}...")
        url = f"{API_URL}&page={page}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            print(f"  Reached end of available data at page {page}")
            break
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching page {page}: {e}")
            break
        
        games = data.get('games', [])
        if not games:
            break
            
        all_games.extend(games)
        print(f"  Found {len(games)} games on page {page} (total: {len(all_games)})")
        
        # Check if there are more pages
        if len(games) < data.get('per_page', 50):
            break
            
        page += 1
    
    print(f"Total games fetched: {len(all_games)}")
    return all_games

def build_game_lookup(api_games):
    """Build a lookup dictionary keyed by date+opponent name"""
    lookup = {}
    
    for game in api_games:
        # Only process 1v1 games
        if sum(len(team) for team in game['teams']) != 2:
            continue
        
        date_time = datetime.fromisoformat(game['started_at'].replace('Z', '+00:00'))
        formatted_date = date_time.strftime("%Y-%m-%d %H:%M")
        
        player = next((p for team in game['teams'] for p in team if p['player']['profile_id'] == TITUS_PROFILE_ID), None)
        opponent = next((p for team in game['teams'] for p in team if p['player']['profile_id'] != TITUS_PROFILE_ID), None)
        
        if player and opponent:
            opponent_name = opponent['player']['name']
            game_id = game['game_id']
            key = f"{formatted_date}_{opponent_name}"
            lookup[key] = game_id
    
    print(f"Built lookup for {len(lookup)} games")
    return lookup

def update_games_file(game_lookup):
    """Update games.md with aoe4world links"""
    with open(GAMES_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the table
    table_start = next((i for i, line in enumerate(lines) if '| Date and Time | Result | Matchup |' in line), -1)
    if table_start == -1:
        print("Could not find games table")
        return
    
    updated_count = 0
    
    for i in range(table_start + 2, len(lines)):
        line = lines[i]
        
        # Skip non-table lines
        if not line.strip() or not line.startswith('|'):
            continue
        
        parts = [part.strip() for part in line.split('|')]
        if len(parts) < 4:
            continue
        
        date_time_cell = parts[1]
        matchup_cell = parts[3]
        
        # Skip if already has aoe4world link (look for !AoE4World marker)
        if '!AoE4World' in date_time_cell or 'time.png' in date_time_cell:
            continue
        
        # Skip if it has YouTube link (we don't want to overwrite those)
        if '!YouTube' in date_time_cell or 'youtube.svg' in date_time_cell:
            continue
        
        # Extract plain date (might be wrapped in markdown link already)
        if date_time_cell.startswith('['):
            # Extract date from existing link format
            date_match = re.search(r'\[([^\]]+)\]', date_time_cell)
            if date_match:
                plain_date = date_match.group(1)
            else:
                plain_date = date_time_cell
        else:
            plain_date = date_time_cell
        
        # Extract opponent name from matchup
        opponent_match = re.search(r'\(([^)]+)\)', matchup_cell)
        if not opponent_match:
            continue
        
        opponent_name = opponent_match.group(1)
        key = f"{plain_date}_{opponent_name}"
        
        # Check if we have this game in our lookup
        if key in game_lookup:
            game_id = game_lookup[key]
            game_url = f"https://aoe4world.com/players/{TITUS_PROFILE_ID}-TitusMaximus/games/{game_id}"
            
            # Replace the date with a linked version
            new_date_cell = f"[{plain_date}]({game_url}) ![AoE4World](/images/time.png)"
            parts[1] = new_date_cell
            
            # Reconstruct the line
            lines[i] = '| ' + ' | '.join(parts[1:-1]) + ' |\n'
            updated_count += 1
            
            if updated_count % 10 == 0:
                print(f"Updated {updated_count} games...")
    
    # Write back to file
    with open(GAMES_FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"\nTotal games updated: {updated_count}")

def main():
    print("Fetching all games from aoe4world API...")
    api_games = fetch_all_games_from_api()
    
    print("\nBuilding game lookup...")
    game_lookup = build_game_lookup(api_games)
    
    print("\nUpdating games.md...")
    update_games_file(game_lookup)
    
    print("\nDone! All historical games have been updated with aoe4world links.")

if __name__ == "__main__":
    main()
