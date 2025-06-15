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

app = typer.Typer()
console = Console()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_URL = "https://api.airtable.com/v0/app55zD0LzyJm1Sx3/Songs"
DOCS_DIR = Path("docs")

def fetch_airtable_data() -> List[Dict]:
    """Fetch song data from Airtable."""
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    response = requests.get(AIRTABLE_BASE_URL, headers=headers, params={"maxRecords": 2, "view": "Grid view"})
    response.raise_for_status()
    return response.json()["records"]

def get_song_file_path(title: str, language: str) -> Optional[Path]:
    """Get the path to the song's markdown file."""
    # Convert title to filename format
    filename = f"{title}.md"
    file_path = DOCS_DIR / language.lower() / filename
    return file_path if file_path.exists() else None

def update_song_tags(file_path: Path, sung_as: List[str], occasion: List[str], song_type: List[str]) -> tuple[bool, str]:
    """Update the tags section in the markdown file using python-frontmatter."""
    error = None
    try:
        post = frontmatter.load(file_path)
        new_content = post.content

        tags = set()
        if sung_as:
            tags.update(sung_as)
        if occasion:
            tags.update(occasion)
        if song_type:
            tags.update(song_type)

        # Split content into lines, add 2 spaces to non-empty lines, and rejoin
        new_content = '\n'.join(line + '  ' if line.strip() else line for line in post.content.splitlines())

        if post['tags'] == sorted(tags) and post.content == new_content:
            return False, error
        
        post['tags'] = sorted(tags)
        frontmatter.dump(post, file_path)

        return True, error
    except Exception as e:
        error = str(e)
        console.print(f"[red]Error updating {file_path}: {str(e)}[/red]")
        return False, error

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
    table.add_column("Status", style="green", width=8, justify="center")
    table.add_column("Details", style="yellow", width=20, justify="left")
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
            
            status, error = update_song_tags(file_path, sung_as, occasion, song_type)

            if status:
                table.add_row("🟡", f"Updated {len(sung_as) + len(occasion) + len(song_type)} tags", title)
            else:
                if error:
                    table.add_row("🔴", f"Failed to update tags: {error}", title)
                else:
                    table.add_row("🟢", "No update needed", title)
            
            progress.update(task, advance=1)
    
    console.print(table)

    # # Print missing files summary
    # if missing_files:
    #     console.print("\n[bold red]Songs missing in the filesystem:[/bold red]")
    #     for title in missing_files:
    #         console.print(f"- {title}")
    # else:
    #     console.print("\n[bold green]All songs found in the filesystem![/bold green]")

def main():
    app()

if __name__ == "__main__":
    main() 