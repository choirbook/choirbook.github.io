#!/usr/bin/env python3

import os
import json
import requests
from typing import List, Dict, Optional
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

app = typer.Typer()
console = Console()

AIRTABLE_API_KEY = "patVxK8cJcu5vZfqL.deece2a43521a3b6970db409347b2691f9ea81b58cb03dfa0b2933497cdcc1ab"
AIRTABLE_BASE_URL = "https://api.airtable.com/v0/app55zD0LzyJm1Sx3/Songs"
DOCS_DIR = Path("docs")

def fetch_airtable_data() -> List[Dict]:
    """Fetch song data from Airtable."""
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    response = requests.get(AIRTABLE_BASE_URL, headers=headers, params={"maxRecords": 50, "view": "Grid view"})
    response.raise_for_status()
    return response.json()["records"]

def get_song_file_path(title: str, language: str) -> Optional[Path]:
    """Get the path to the song's markdown file."""
    # Convert title to filename format
    filename = f"{title}.md"
    file_path = DOCS_DIR / language.lower() / filename
    return file_path if file_path.exists() else None

def update_song_tags(file_path: Path, sung_as: List[str], occasion: List[str], song_type: List[str]) -> bool:
    """Update the tags section in the markdown file."""
    try:
        content = file_path.read_text()
        
        # Extract frontmatter
        if not content.startswith("---"):
            return False
            
        parts = content.split("---", 2)
        if len(parts) < 3:
            return False
            
        # Process tags
        tags = set()
        if sung_as:
            tags.update(sung_as)
        if occasion:
            tags.update(occasion)
        if song_type:
            tags.update(song_type)
            
        # Create new frontmatter
        new_frontmatter = "---\ntags:\n"
        for tag in sorted(tags):
            new_frontmatter += f"  - {tag}\n"
        new_frontmatter += "---\n"
        
        # Update file
        new_content = new_frontmatter + parts[2]
        file_path.write_text(new_content)
        return True
    except Exception as e:
        console.print(f"[red]Error updating {file_path}: {str(e)}[/red]")
        return False

@app.command()
def update():
    """Update song tags from Airtable data."""
    console.print("[bold blue]Fetching data from Airtable...[/bold blue]")
    
    try:
        records = fetch_airtable_data()
    except Exception as e:
        console.print(f"[red]Error fetching data from Airtable: {str(e)}[/red]")
        raise typer.Exit(1)
    
    table = Table(title="Song Updates")
    table.add_column("Title", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
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
                table.add_row(title, "❌", "File not found")
                missing_files.append(title)
                progress.update(task, advance=1)
                continue
            
            sung_as = fields.get("Sung as", [])
            occasion = fields.get("Ocassion", [])
            song_type = fields.get("Type", [])
            
            if update_song_tags(file_path, sung_as, occasion, song_type):
                table.add_row(title, "✅", f"Updated {len(sung_as) + len(occasion) + len(song_type)} tags")
            else:
                table.add_row(title, "❌", "Failed to update tags")
            
            progress.update(task, advance=1)
    
    console.print(table)

    # Print missing files summary
    if missing_files:
        console.print("\n[bold red]Songs missing in the filesystem:[/bold red]")
        for title in missing_files:
            console.print(f"- {title}")
    else:
        console.print("\n[bold green]All songs found in the filesystem![/bold green]")

def main():
    app()

if __name__ == "__main__":
    main() 