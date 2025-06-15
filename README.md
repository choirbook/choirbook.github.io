# Choir Book

A searchable compilation of church songs and hymns, organized by language and category. This repository contains the source code for the [Choir Book website](https://choirbook.github.io).

## Features

- Searchable collection of church songs
- Organized by language (English, Hindi, Malayalam)
- Categorized by usage (Entrance, Communion, Recessional, etc.)
- Dark/Light mode support
- Mobile-friendly design

## Local Development

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/choirbook/choirbook.github.io.git
   cd choirbook.github.io
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the local development server:
   ```bash
   mkdocs serve
   ```

5. Open your browser and visit `http://localhost:8000`

### Project Structure

- `mkdocs.yml` - Main configuration file
- `docs/` - Documentation and song content
  - `english/` - English songs
  - `hindi/` - Hindi songs
  - `malayalam/` - Malayalam songs

### Adding New Songs

1. Create a new markdown file in the appropriate language directory under `docs/`
2. Use the following front matter format:
   ```markdown
   ---
   tags:
     - communion
   ---
   ```
3. Format the lyrics with proper line breaks (use two spaces at the end of each line)
4. Add appropriate categories at the bottom of the file

### Theme

This site uses the [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme, which provides:
- Clean, modern design
- Dark/Light mode toggle
- Advanced search functionality
- Mobile responsiveness
- Instant loading
- SEO optimization

## Contributing

1. Fork the repository
2. Create a new branch for your changes
3. Make your changes
4. Submit a pull request
