#!/usr/bin/env python3
"""
Convert link format in games.md and halloffame.md from:
  [date](url) ![Icon](/path)
to:
  date [![Icon](/path)](url)
"""

import re

GAMES_FILE = 'content/games.md'
HALL_OF_FAME_FILE = 'content/halloffame.md'

def convert_file_link_format(file_path):
    """Convert all date links to icon links in a file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match: [date](url) ![Icon](/path)
    # Captures: date, url, icon_full
    pattern = r'\[([^\]]+)\]\(([^)]+)\) (!\[[^\]]+\]\([^)]+\))'
    
    def replace_func(match):
        date = match.group(1)
        url = match.group(2)
        icon_full = match.group(3)  # e.g., ![AoE4World](/images/time.png) or ![YouTube](/images/youtube.svg)
        
        # New format: date [![Icon](/path)](url)
        return f'{date} [{icon_full}]({url})'
    
    new_content = re.sub(pattern, replace_func, content)
    
    # Only write if content changed
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Converted link formats in {file_path}")
    else:
        print(f"No conversions needed in {file_path}")

def convert_link_format():
    """Convert all date links to icon links in games.md and halloffame.md"""
    convert_file_link_format(GAMES_FILE)
    convert_file_link_format(HALL_OF_FAME_FILE)

if __name__ == '__main__':
    convert_link_format()
