#!/usr/bin/env python3
"""
Convert link format in games.md from:
  [date](url) ![Icon](/path)
to:
  date [![Icon](/path)](url)
"""

import re

GAMES_FILE = 'content/games.md'

def convert_link_format():
    """Convert all date links to icon links in games.md"""
    with open(GAMES_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match: [date](url) ![Icon](/path)
    # Captures: date, url, icon_text, icon_path
    pattern = r'\[([^\]]+)\]\(([^)]+)\) (!\[[^\]]+\]\([^)]+\))'
    
    def replace_func(match):
        date = match.group(1)
        url = match.group(2)
        icon = match.group(3)  # e.g., ![AoE4World](/images/time.png)
        
        # New format: date [![Icon](/path)](url)
        return f'{date} [![{icon[2:-1].split("](")[0]}]({icon[2:-1].split("](")[1]})]({url})'
    
    # Simpler approach - extract the parts we need
    pattern = r'\[([^\]]+)\]\(([^)]+)\) (!\[[^\]]+\]\([^)]+\))'
    
    def replace_func(match):
        date = match.group(1)
        url = match.group(2)
        icon_full = match.group(3)  # e.g., ![AoE4World](/images/time.png) or ![YouTube](/images/youtube.svg)
        
        # New format: date [![...](...))](...url...)
        return f'{date} [{icon_full}]({url})'
    
    new_content = re.sub(pattern, replace_func, content)
    
    with open(GAMES_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Converted all link formats in games.md")

if __name__ == '__main__':
    convert_link_format()
