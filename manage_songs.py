#!/usr/bin/env python3

import os
import json
import requests
import yaml
from typing import List, Dict, Optional
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
import frontmatter
import difflib

app = typer.Typer()
console = Console()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_URL = "https://api.airtable.com/v0/app55zD0LzyJm1Sx3/Songs"
DOCS_DIR = Path("docs")

def fetch_airtable_data() -> List[Dict]:
    """Fetch song data from Airtable."""
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    response = requests.get(AIRTABLE_BASE_URL, headers=headers, params={"maxRecords": 100, "view": "Grid view"})
    response.raise_for_status()
    return response.json()["records"]

def get_song_file_path(title: str, language: str) -> Optional[Path]:
    """Get the path to the song's markdown file."""
    # Convert title to filename format
    filename = f"{title}.md"
    file_path = DOCS_DIR / language.lower() / filename
    return file_path if file_path.exists() else None

def update_song_tags_and_content(file_path: Path, sung_as: List[str], occasion: List[str], song_type: List[str]) -> tuple[bool, str]:
    """Update the tags section and normalize content formatting in the markdown file using python-frontmatter."""
    try:
        post = frontmatter.load(file_path)

        # --- Tag update logic ---
        # Combine all tags from sung_as, occasion, and song_type. Compare with existing tags.
        # If there are any additions or removals, update the tags and prepare a message describing the change.
        tags = set(sung_as or []) | set(occasion or []) | set(song_type or [])
        existing_tags = set(post.get('tags', []))
        added_tags = tags - existing_tags
        removed_tags = existing_tags - tags
        tag_message = []
        if added_tags:
            tag_message.append(f"Added: {', '.join(sorted(added_tags))}")
        if removed_tags:
            tag_message.append(f"Removed: {', '.join(sorted(removed_tags))}")
        if tag_message:
            post['tags'] = sorted(tags)
        message = " | ".join(tag_message) if tag_message else ""

        # --- Content normalization logic ---
        # For each line in the content:
        #   - Remove all trailing spaces
        #   - If the line is not empty, add exactly two spaces to the end
        #   - If the line is empty, keep it empty
        # Preserve the original file's newline behavior
        orig_lines = post.content.splitlines()
        if not orig_lines:
            new_content = post.content

        # Normalize all lines except the last one
        norm_lines = [line.rstrip() + '  ' if line.rstrip() else '' for line in orig_lines[:-1]]
        # Handle the last line - don't add trailing spaces to preserve original behavior
        last_line = orig_lines[-1]
        norm_lines.append(last_line.rstrip())
        
        # Preserve original newline behavior: only add final newline if original had one
        if post.content.endswith('\n'):
            new_content = "\n".join(norm_lines) + "\n"
        else:
            new_content = "\n".join(norm_lines)
        
        # Check if content actually needs updating
        content_needs_update = post.content != new_content
        
        if content_needs_update:
            post.content = new_content
            if message == "":
                message = "Updated content spacing"
            else:
                message += " | Updated content spacing"

        # Only write if something changed
        if tag_message or content_needs_update:
            frontmatter.dump(post, file_path)
        return True, message
    except Exception as e:
        message = f"[red]Error updating {file_path}: {str(e)}[/red]"
        return False, message

@app.command()
def update():
    """Update song tags from Airtable data."""
    console.print("[bold blue]Fetching data from Airtable...[/bold blue]")
    
    try:
        records = fetch_airtable_data()
    except Exception as e:
        console.print(f"[red]Error fetching data from Airtable: {str(e)}[/red]")
        raise typer.Exit(1)
    
    table = Table(title="Song Updates", show_header=True, header_style="bold magenta", box=None)
    table.add_column("Status", style="green", width=10, justify="center")
    table.add_column("Details", style="yellow", width=30, justify="left")
    table.add_column("Title", style="cyan", width=80, no_wrap=False)
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Processing songs...", total=len(records))
        
        missing_files = []  # List to store missing song titles
        for record in records:
            fields = record["fields"]
            title = fields.get("title")
            language = fields.get("language", "English")
            
            if not title:
                continue
                
            file_path = get_song_file_path(title, language)
            if not file_path:
                table.add_row("🔴", "File not found", title)
                missing_files.append(title)
                progress.update(task, advance=1)
                continue
            
            sung_as = fields.get("Sung as", [])
            occasion = fields.get("Ocassion", [])
            song_type = fields.get("Type", [])
            
            status, message = update_song_tags_and_content(file_path, sung_as, occasion, song_type)

            if status:
                if message:
                    table.add_row("🟡", message, title)
                else:
                    table.add_row("🟢", "No update needed", title)
            else:
                table.add_row("🔴", f"Failed to update: {message}", title)
              
            progress.update(task, advance=1)
    
    console.print(table)

def main():
    app()

if __name__ == "__main__":
    main() 