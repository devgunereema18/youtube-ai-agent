# AI Video Agent

Automated AI-powered pipeline for creating and publishing YouTube videos.

```
VidIQ (Research & Prompt) --> HeyGen AI (Video Creation) --> YouTube (Upload)
```

## Pipeline Flow

1. **VidIQ Agent** - Researches trending topics, generates SEO-optimized titles, descriptions, tags, and video scripts
2. **HeyGen Agent** - Takes the script, selects an AI avatar, generates a professional video
3. **YouTube Agent** - Uploads the rendered video with all metadata to your YouTube channel

## Setup

### 1. Install Dependencies

```bash
cd youtube-ai-agent
pip install -r requirements.txt
```

### 2. Get API Keys

| Service | Where to Get |
|---------|-------------|
| VidIQ | https://vidiq.com/mcp/ |
| HeyGen | https://app.heygen.com/settings (API section) |
| YouTube | Google Cloud Console - YouTube Data API v3 |
| OpenAI (optional) | https://platform.openai.com/api-keys |

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. YouTube OAuth Setup

1. Go to Google Cloud Console (https://console.cloud.google.com)
2. Create a project and enable YouTube Data API v3
3. Create OAuth 2.0 credentials (Desktop Application)
4. Add your Client ID and Secret to `.env`

## Usage

### Single Video

```bash
python main.py --topic "Artificial Intelligence in 2024" --style educational
python main.py --topic "Python for Beginners" --style tutorial --privacy public
python main.py --topic "Tech News" --no-upload
```

### Batch Processing

```bash
echo "Machine Learning Basics" > topics.txt
echo "Python Tips and Tricks" >> topics.txt
python main.py --batch topics.txt --niche technology --style educational
```

### Utility Commands

```bash
python main.py --validate
python main.py --list-avatars
python main.py --list-voices
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--topic` | Video topic | Required |
| `--batch` | Path to topics file | - |
| `--niche` | Content niche | technology |
| `--style` | Video style | educational |
| `--avatar` | HeyGen avatar ID | default |
| `--voice` | HeyGen voice ID | default |
| `--privacy` | YouTube privacy | private |
| `--no-upload` | Skip YouTube upload | False |

## Project Structure

```
youtube-ai-agent/
├── main.py                 # Entry point & CLI
├── config.py               # Configuration loader
├── requirements.txt        # Python dependencies
├── .env.example            # Template for API keys
├── agents/
│   ├── __init__.py
│   ├── vidiq_agent.py      # VidIQ prompt generation
│   ├── heygen_agent.py     # HeyGen video creation
│   ├── youtube_agent.py    # YouTube upload
│   └── orchestrator.py     # Pipeline coordinator
└── output/                 # Downloaded videos & results
```

## Security Notes

- API keys stored in `.env` (never commit this file)
- YouTube OAuth tokens saved in `youtube_token.json`
- Videos default to `private` to prevent accidental public publishing

## License

MIT
