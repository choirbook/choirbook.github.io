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

- Ruby (version 2.6 or higher)
- Bundler
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/choirbook/choirbook.github.io.git
   cd choirbook.github.io
   ```

2. Install dependencies:
   ```bash
   bundle install --path vendor/bundle
   ```

3. Start the local development server:
   ```bash
   bundle exec jekyll serve
   ```

4. Open your browser and visit `http://localhost:4000`

### Project Structure

- `_config.yml` - Main configuration file
- `_sass/` - Custom styles
- `english/` - English songs
- `hindi/` - Hindi songs
- `malayalam/` - Malayalam songs

### Adding New Songs

1. Create a new markdown file in the appropriate language directory
2. Use the following front matter format:
   ```markdown
   ---
   layout: default
   title: "Song Title"
   parent: Language
   ---
   ```
3. Format the lyrics with proper line breaks (use two spaces at the end of each line)
4. Add appropriate categories at the bottom of the file

### Theme

This site uses the [Just the Docs](https://just-the-docs.github.io/just-the-docs/) theme, which provides:
- Clean, modern design
- Dark/Light mode toggle
- Search functionality
- Mobile responsiveness

## Contributing

1. Fork the repository
2. Create a new branch for your changes
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License. 