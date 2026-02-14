import os
import re
from html import unescape

def clean_html(text):
    # Replace <br />, <br>, etc with newline
    text = re.sub(r'<br\s*/?>', '
', text)
    # Strip all other tags
    text = re.sub(r'<[^>]+>', '', text)
    # Unescape HTML entities (e.g. &nbsp;)
    text = unescape(text)
    # Strip leading/trailing spaces from each line in the paragraph
    lines = [line.strip() for line in text.split('
')]
    return '
'.join(lines)

def process_dir(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.txt'):
                file_path = os.path.join(root, filename)
                print(f"Refining {file_path}...")
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                new_content = []
                current_para = []
                
                for line in lines:
                    stripped = line.strip()
                    
                    # Detect markers like headers or horizontal rules
                    if stripped.startswith('===') or stripped.startswith('---'):
                        if current_para:
                            new_content.append(' '.join(current_para))
                            current_para = []
                        new_content.append(stripped)
                        new_content.append('') # Add blank line after header underline
                        continue
                    
                    if not stripped:
                        if current_para:
                            new_content.append(' '.join(current_para))
                            current_para = []
                        new_content.append('')
                        continue
                    
                    # It's a text line
                    # We want to maintain manual newlines if they were intended, 
                    # but the previous script joined them somewhat weirdly or left spaces.
                    # Actually, let's just use a simpler approach:
                    # If the previous script output had a leading space, we remove it.
                    new_content.append(stripped)
                    new_content.append('') # Ensure double newlines between everything for now
                
                # Cleanup: remove multiple consecutive empty lines
                final_content = []
                last_empty = False
                for line in new_content:
                    if line == '':
                        if not last_empty:
                            final_content.append(line)
                            last_empty = True
                    else:
                        final_content.append(line)
                        last_empty = False
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('
'.join(final_content))

# Actually, the previous script's logic was flawed in how it joined paragraphs.
# Let's just re-run the conversion from the original scrape JSONs if they still exist.
# Oh wait, I deleted them. I will have to fix the TXT files directly or scrape again.
# Scraping again is safer to get the structure right.

# Wait, I can just use the index to scrape again, it's fast.
print("Re-scraping and converting with improved formatting...")
# I'll re-run the logic but with better formatting.
