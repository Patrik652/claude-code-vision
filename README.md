# Claude Code Vision - Visual Feedback System

**Add visual context to your Claude Code sessions** - Capture screenshots and send them to Claude for analysis, debugging, and design feedback.

## Features

- 🖼️ **Full Screen Capture** - `/vision` command captures your screen and analyzes it
- 🎯 **Area Selection** - `/vision.area` for focused region capture with graphical or coordinate input
- 🔄 **Auto-Monitoring** - `/vision.auto` for continuous observation
- 🔒 **Privacy Controls** - Configure exclusion zones for sensitive information
- 🤖 **AI Provider Choice** - Use Claude API or Google Gemini API with automatic fallback
- 🖥️ **Multi-Monitor Support** - Capture from specific monitors with `--monitor` flag
- 🐧 **Linux Support** - Works on X11 and Wayland desktop environments
- ⚡ **Auto-Detection** - Automatically detects and uses available screenshot tools
- 🛠️ **Diagnostic Tools** - Built-in commands for testing and troubleshooting

## Quick Installation

### Prerequisites

- Claude Code installed and OAuth configured
- Linux with X11 or Wayland desktop environment
- Python 3.8 or later
- sudo access (for installing screenshot tools)

### Install System Dependencies

**For X11 (most common):**
```bash
# Ubuntu/Debian
sudo apt install scrot xrectsel -y

# Fedora/RHEL
sudo dnf install scrot xrectsel -y

# Arch
sudo pacman -S scrot xrectsel --noconfirm
```

**For Wayland:**
```bash
# Ubuntu/Debian
sudo apt install grim slurp -y

# Fedora/RHEL
sudo dnf install grim slurp -y

# Arch
sudo pacman -S grim slurp --noconfirm
```

### Install Claude Code Vision

```bash
# Clone repository
git clone https://github.com/Patrik652/claude-code-vision.git
cd claude-code-vision

# Install with pip
pip install -e .
```

### Initialize and Verify

```bash
# Generate default config
claude-vision --init

# Run diagnostic check
claude-vision --doctor
```

## Usage

### Basic Commands

```bash
# Capture full screen and analyze
/vision "What's on my screen?"

# Capture from specific monitor
/vision --monitor 1 "What's on my second screen?"

# Capture specific area (graphical selection)
/vision.area "Analyze this error dialog"

# Capture area with coordinates
/vision.area --coords "100,100,800,600" "What's in this region?"

# Start continuous monitoring
/vision.auto

# Stop monitoring
/vision.stop
```

### Utility Commands

```bash
# Initialize configuration
claude-vision --init

# Run diagnostics
claude-vision --doctor

# List available monitors
claude-vision --list-monitors

# Validate configuration
claude-vision --validate-config

# Test screenshot capture
claude-vision --test-capture
```

### AI Provider Configuration

Claude Code Vision supports both Claude API and Google Gemini API.

**Configure Gemini API (recommended for speed and cost):**

1. Get API key from: https://aistudio.google.com/apikey
2. Edit `~/.config/claude-code-vision/config.yaml`:

```yaml
ai_provider:
  provider: gemini  # Use 'claude' or 'gemini'
  fallback_to_gemini: true  # Enable automatic fallback

gemini:
  api_key: 'YOUR_GEMINI_API_KEY'
  model: gemini-2.0-flash-exp  # Fast and efficient
```

**Or set via environment variable:**
```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

See [GEMINI_SETUP.md](GEMINI_SETUP.md) for detailed setup instructions.

### Privacy Configuration

Edit `~/.config/claude-code-vision/config.yaml` to configure privacy zones:

```yaml
privacy:
  enabled: true
  zones:
    - name: "password_manager"
      x: 1500
      y: 0
      width: 420
      height: 100
```

## Documentation

- 📘 **[Quickstart Guide](specs/002-claude-code-vision/quickstart.md)** - Complete installation and usage guide
- 📋 **[Feature Specification](specs/002-claude-code-vision/spec.md)** - Detailed feature requirements
- 🏗️ **[Implementation Plan](specs/002-claude-code-vision/plan.md)** - Technical architecture
- 📊 **[Data Model](specs/002-claude-code-vision/data-model.md)** - Entity definitions
- 🔌 **[API Contracts](specs/002-claude-code-vision/contracts/)** - Interface specifications
- 📝 **[Changelog](CHANGELOG.md)** - Recent updates and release notes
- ✅ **[Production Smoke Test](PRODUCTION_SMOKE_TEST.md)** - Deployment validation and rollback

## Architecture

- **Language**: Python 3.8+
- **Key Dependencies**: Pillow, PyYAML, requests, click, google-generativeai
- **Screenshot Tools**: scrot (X11), grim (Wayland), ImageMagick (fallback)
- **AI Providers**: Claude API (via OAuth) or Google Gemini API
- **Integration**: Works seamlessly with Claude Code slash commands

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
black .
ruff check .
mypy src/
```

### Project Structure

```
src/
├── models/      # Data entities (Screenshot, Configuration, etc.)
├── services/    # Core services (capture, processing, API client)
├── cli/         # CLI commands
└── lib/         # Utilities (logging, detection, exceptions)

tests/
├── contract/    # Contract tests for interfaces
├── integration/ # End-to-end workflow tests
└── unit/        # Unit tests for components
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow test-first development (write tests before implementation)
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/Patrik652/claude-code-vision/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Patrik652/claude-code-vision/discussions)

## Roadmap

- [x] Core screenshot capture (X11/Wayland)
- [x] Claude API integration
- [x] Google Gemini API integration
- [x] Privacy zones
- [x] Area selection with graphical and coordinate input
- [x] Auto-monitoring mode
- [x] Multi-monitor support
- [x] Diagnostic and testing utilities
- [ ] Windows support
- [ ] macOS support
- [ ] Video recording
- [ ] Screenshot history
- [ ] Browser extension integration

## Acknowledgments

Built with ❤️ for the Claude Code community. Powered by [Claude AI](https://claude.ai/) and [Anthropic](https://anthropic.com/).

---

**Made with [Claude Code](https://claude.com/claude-code)** 🤖
