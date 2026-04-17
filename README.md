# Loggbok Robot 📖⚓

Generate creative and authentic ship log entries in Norwegian using weather data and location information from the Sørland fjords.

## Overview

This tool combines:
- **Real location data**: Randomly selected lighthouses from `fyrlykter_sorlandet.geojson`
- **Real weather data**: Current conditions fetched from the Met.no API
- **AI generation**: Ollama-powered creative generation in the style of 1500-1800 ship logs
- **Historical authenticity**: Grounded by real log entry examples from the era

## Installation

### Using uv (recommended)

```bash
# Install dependencies
uv sync

# Run the script
uv run main.py
```


## Prerequisites

1. **Ollama**: Must be running locally on `localhost:11434`
   - Download: https://ollama.ai
   - Run: `ollama serve`
   - Pull a model: `ollama pull mistral` (or another model)

2. **Data files**:
   - `fyrlykter_sorlandet.geojson` - Lighthouse locations (included)
   - `logsample.md` - Historical log entries for reference (included)

## Usage

### Basic usage (output to terminal)

```bash
uv run main.py
```

### Save to markdown file

```bash
uv run main.py --output markdown
```

Creates a markdown file in `logs/` directory with timestamp and adds entry to `registry.json`.

### Send to webhook

```bash
uv run main.py --output webhook --webhook-url https://example.com/webhook
```

### Specify a different Ollama model

```bash
uv run main.py --model neural-chat
# or
uv run main.py --output markdown --model mistral
```

## Output Format

### Shell output
```
📍 Ternholmen (58.844°, 9.490°)
🌦️ Temperature: 12°C | Wind speed: 4.5 m/s | Humidity: 72%

📖 Dagbokoppføring:
Oktober 15: Klart vær med mild bris fra sørvest. Alle seil satt. Styrende NØ langs kysten.
Så flere hbirder. Sjøen flat. Moderat strøm. Alt vel om bord. Så andre skip på avstanden.
```

### Markdown output
Creates `logs/skipsdagbok_YYYYMMDD_HHMMSS.md` with metadata and log entry.

### Webhook output
Sends JSON payload:
```json
{
  "timestamp": "2025-04-17T14:30:00",
  "location": "Ternholmen",
  "coordinates": {
    "latitude": 58.844,
    "longitude": 9.490
  },
  "log_entry": "Oktober 15: Klart vær..."
}
```

## Architecture

### Main Components

1. **Location Data**: Random selection from `fyrlykter_sorlandet.geojson`
2. **Weather API**: Met.no nowcast API for real conditions
3. **LLM Generation**: Ollama with Mistral (or custom model)
4. **Output Options**: 
   - Echo to shell (default)
   - Save to markdown with registry
   - Call webhook endpoint

### Prompt Strategy

The system uses:
- A detailed system prompt with historical examples from `logsample.md`
- Context: location name, coordinates, weather conditions
- Generates creative but plausible log entries matching the historical style

## Configuration

All options are command-line arguments:

```bash
uv run main.py --help
```

Options:
- `--output`: shell, markdown, or webhook (default: shell)
- `--webhook-url`: URL for webhook output
- `--model`: Ollama model name (default: mistral)

## Project Structure

```
loggbok_robot/
├── main.py                          # Main script
├── pyproject.toml                   # Project config (uv)
├── README.md                        # This file
├── fyrlykter_sorlandet.geojson     # Lighthouse data
├── logsample.md                     # Historical examples
├── logs/                            # Output directory (created on markdown output)
├── registry.json                    # Entries registry (created on markdown output)
└── [other files]
```

## Examples

### Generate and display in terminal
```bash
uv run main.py
```

### Generate and save to file
```bash
uv run main.py --output markdown
# Check registry.json to see all saved entries
```

### Automated generation with webhook
```bash
# Set up a cron job or similar
uv run main.py --output webhook --webhook-url https://myserver.com/logs
```

## Notes

- The system is designed to be simple and modular
- All dependencies are Python-only (no external commands needed)
- Weather data is real-time from Met.no
- Log generation requires Ollama running locally
- Each run selects a different random location and generates unique content

## Future Enhancements

- Database storage option instead of JSON registry
- Multiple language support
- Customizable historical periods
- Ship type specification (whaling, merchant, fishing, etc.)
- Batch generation mode

---

**Author**: Created for autonomous ship log generation 
**License**: MIT
