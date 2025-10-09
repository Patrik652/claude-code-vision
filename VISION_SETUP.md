# Claude Code Vision Setup

## ✅ Current Status

The `/vision` command is **installed and working**, but needs an **Anthropic API key** to function.

## 🔧 Setup Required

### Option 1: Use Anthropic API Key (Recommended)

1. Get your Anthropic API key from: https://console.anthropic.com/settings/keys

2. Add to your config:
```bash
nano ~/.config/claude-code-vision/config.yaml
```

Add this section:
```yaml
claude_code:
  api_key: "your-api-key-here"  # Replace with your actual API key
  api_endpoint: https://api.anthropic.com/v1/messages
```

Or set as environment variable:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Option 2: Current OAuth Token (Not Supported)

The OAuth token in `~/.claude/.credentials.json` is for Claude.ai web authentication and **cannot be used** with the Anthropic API directly.

## 🧪 Test Installation

After adding your API key:

```bash
source venv/bin/activate
claude-vision vision "What do you see on my screen?"
```

## 📋 Features Available

- ✅ Screenshot capture working
- ✅ Image optimization working
- ✅ Privacy zones configured
- ✅ Multi-monitor support
- ⏳ API authentication (needs API key)

## 💡 Alternative: Use Claude Code's Built-in Vision

If you don't want to set up a separate API key, you can use images with Claude Code directly:

1. Take a screenshot manually
2. Drag and drop the image into Claude Code chat
3. Ask your question

## 🐛 Troubleshooting

```bash
# Run diagnostics
claude-vision doctor

# Validate config
claude-vision --validate-config

# Check logs
tail -f ~/.config/claude-code-vision/vision.log
```

## 📚 Documentation

- Anthropic API: https://docs.anthropic.com/claude/reference/getting-started-with-the-api
- Vision capabilities: https://docs.anthropic.com/claude/docs/vision
