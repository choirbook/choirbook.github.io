#!/usr/bin/env python3

import os
import json
import requests
import yaml
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
import frontmatter
import difflib

# Configuration constants
class Config:
    AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
    AIRTABLE_BASE_URL = "https://api.airtable.com/v0/app55zD0LzyJm1Sx3/Songs"
    DOCS_DIR = Path("docs")
    MAX_RECORDS = 100
    VIEW_NAME = "Grid view"

# Custom exceptions
class SongManagementError(Exception):
    """Base exception for song management operations."""
    pass

class AirtableAPIError(SongManagementError):
    """Exception raised when Airtable API operations fail."""
    pass

class FileOperationError(SongManagementError):
    """Exception raised when file operations fail."""
    pass

# Status enum for better type safety
class UpdateStatus(Enum):
    SUCCESS = "🟢"
    UPDATED = "🟡"
    FAILED = "🔴"
    NOT_FOUND = "🔴"

@dataclass
class SongData:
    """Data class to represent song information from Airtable."""
    title: str
    language: str = "English"
    sung_as: List[str] = None
    occasion: List[str] = None
    song_type: List[str] = None
    
    def __post_init__(self):
        self.sung_as = self.sung_as or []
        self.occasion = self.occasion or []
        self.song_type = self.song_type or []
    
    @property
    def all_tags(self) -> set:
        """Get all tags combined from sung_as, occasion, and song_type."""
        return set(self.sung_as) | set(self.occasion) | set(self.song_type)

@dataclass
class UpdateResult:
    """Result of a song update operation."""
    status: UpdateStatus
    message: str
    title: str

class AirtableClient:
    """Handles all Airtable API interactions."""
    
    def __init__(self, api_key: str, base_url: str):
        if not api_key:
            raise AirtableAPIError("AIRTABLE_API_KEY environment variable is required")
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def fetch_songs(self, max_records: int = Config.MAX_RECORDS, view: str = Config.VIEW_NAME) -> List[Dict]:
        """Fetch song data from Airtable."""
        try:
            params = {"maxRecords": max_records, "view": view}
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()["records"]
        except requests.RequestException as e:
            raise AirtableAPIError(f"Failed to fetch data from Airtable: {str(e)}")

class SongFileManager:
    """Handles file operations for song markdown files."""
    
    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
    
    def get_song_file_path(self, title: str, language: str) -> Optional[Path]:
        """Get the path to the song's markdown file."""
        filename = f"{title}.md"
        file_path = self.docs_dir / language.lower() / filename
        return file_path if file_path.exists() else None
    
    def update_song_tags(self, file_path: Path, new_tags: set) -> Tuple[bool, str]:
        """Update the tags section in the markdown file."""
        try:
            post = frontmatter.load(file_path)
            existing_tags = set(post.get('tags', []))
            
            added_tags = new_tags - existing_tags
            removed_tags = existing_tags - new_tags
            
            if not added_tags and not removed_tags:
                return False, ""
            
            tag_messages = []
            if added_tags:
                tag_messages.append(f"Added: {', '.join(sorted(added_tags))}")
            if removed_tags:
                tag_messages.append(f"Removed: {', '.join(sorted(removed_tags))}")
            
            post['tags'] = sorted(new_tags)
            frontmatter.dump(post, file_path)
            
            return True, " | ".join(tag_messages)
        except Exception as e:
            raise FileOperationError(f"Failed to update tags: {str(e)}")
    
    def normalize_content_spacing(self, file_path: Path) -> Tuple[bool, str]:
        """Normalize content formatting in the markdown file."""
        try:
            post = frontmatter.load(file_path)
            original_content = post.content
            
            if not original_content:
                return False, ""
            
            lines = original_content.splitlines()
            if not lines:
                return False, ""
            
            # Normalize all lines except the last one
            normalized_lines = [
                line.rstrip() + '  ' if line.rstrip() else '' 
                for line in lines[:-1]
            ]
            # Handle the last line - don't add trailing spaces
            normalized_lines.append(lines[-1].rstrip())
            
            # Preserve original newline behavior
            new_content = "\n".join(normalized_lines)
            if original_content.endswith('\n'):
                new_content += "\n"
            
            if original_content == new_content:
                return False, ""
            
            post.content = new_content
            frontmatter.dump(post, file_path)
            
            return True, "Updated content spacing"
        except Exception as e:
            raise FileOperationError(f"Failed to normalize content: {str(e)}")
    
    def update_song_file(self, file_path: Path, song_data: SongData) -> UpdateResult:
        """Update both tags and content formatting for a song file."""
        try:
            tags_updated, tag_message = self.update_song_tags(file_path, song_data.all_tags)
            content_updated, content_message = self.normalize_content_spacing(file_path)
            
            messages = [msg for msg in [tag_message, content_message] if msg]
            
            if tags_updated or content_updated:
                status = UpdateStatus.UPDATED
                message = " | ".join(messages)
            else:
                status = UpdateStatus.SUCCESS
                message = "No update needed"
                
            return UpdateResult(status, message, song_data.title)
            
        except (FileOperationError, Exception) as e:
            return UpdateResult(UpdateStatus.FAILED, str(e), song_data.title)

class SongDataParser:
    """Parses Airtable records into SongData objects."""
    
    @staticmethod
    def parse_record(record: Dict) -> Optional[SongData]:
        """Parse an Airtable record into a SongData object."""
        fields = record.get("fields", {})
        title = fields.get("title")
        
        if not title:
            return None
            
        return SongData(
            title=title,
            language=fields.get("language", "English"),
            sung_as=fields.get("Sung as", []),
            occasion=fields.get("Ocassion", []),  # Note: keeping original typo from Airtable
            song_type=fields.get("Type", [])
        )

class SongUpdater:
    """Main class that orchestrates the song update process."""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.airtable_client = AirtableClient(Config.AIRTABLE_API_KEY, Config.AIRTABLE_BASE_URL)
        self.file_manager = SongFileManager(Config.DOCS_DIR)
        self.parser = SongDataParser()
    
    def update_songs(self) -> None:
        """Update song tags from Airtable data."""
        self.console.print("[bold blue]Fetching data from Airtable...[/bold blue]")
        
        try:
            records = self.airtable_client.fetch_songs()
        except AirtableAPIError as e:
            self.console.print(f"[red]Error fetching data from Airtable: {str(e)}[/red]")
            raise typer.Exit(1)
        
        results = self._process_songs(records)
        self._display_results(results)
    
    def _process_songs(self, records: List[Dict]) -> List[UpdateResult]:
        """Process all song records and return results."""
        results = []
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing songs...", total=len(records))
            
            for record in records:
                song_data = self.parser.parse_record(record)
                if not song_data:
                    progress.update(task, advance=1)
                    continue
                
                result = self._process_single_song(song_data)
                results.append(result)
                progress.update(task, advance=1)
        
        return results
    
    def _process_single_song(self, song_data: SongData) -> UpdateResult:
        """Process a single song and return the result."""
        file_path = self.file_manager.get_song_file_path(song_data.title, song_data.language)
        
        if not file_path:
            return UpdateResult(UpdateStatus.NOT_FOUND, "File not found", song_data.title)
        
        return self.file_manager.update_song_file(file_path, song_data)
    
    def _display_results(self, results: List[UpdateResult]) -> None:
        """Display the results in a formatted table."""
        table = Table(
            title="Song Updates", 
            show_header=True, 
            header_style="bold magenta", 
            box=None
        )
        table.add_column("Status", style="green", width=10, justify="center")
        table.add_column("Details", style="yellow", width=30, justify="center")
        table.add_column("Title", style="cyan", width=80, no_wrap=False)
        
        for result in results:
            table.add_row(result.status.value, result.message, result.title)
        
        self.console.print(table)

# CLI setup
app = typer.Typer()
console = Console()

@app.command()
def update():
    """Update song tags from Airtable data."""
    updater = SongUpdater(console)
    updater.update_songs()

def main():
    app()

if __name__ == "__main__":
    main() 