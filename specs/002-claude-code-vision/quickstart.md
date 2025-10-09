# Quickstart Guide: Claude Code Vision

**Get visual feedback in Claude Code in 10 minutes.**

---

## Prerequisites

- ✅ Claude Code installed and OAuth configured
- ✅ Linux with X11 or Wayland desktop environment
- ✅ Python 3.8 or later
- ✅ sudo access (for installing screenshot tools)

---

## Installation

### Step 1: Install System Dependencies

**For X11 (most common)**:
```bash
# Ubuntu/Debian
sudo apt install scrot xrectsel -y

# Fedora/RHEL
sudo dnf install scrot xrectsel -y

# Arch
sudo pacman -S scrot xrectsel --noconfirm
```

**For Wayland**:
```bash
# Ubuntu/Debian
sudo apt install grim slurp -y

# Fedora/RHEL
sudo dnf install grim slurp -y

# Arch
sudo pacman -S grim slurp --noconfirm
```

**Universal Fallback** (if unsure):
```bash
sudo apt install imagemagick -y  # Ubuntu/Debian
sudo dnf install ImageMagick -y  # Fedora/RHEL
sudo pacman -S imagemagick --noconfirm  # Arch
```

### Step 2: Install Claude Code Vision

```bash
# Clone repository (or download release)
git clone https://github.com/YOUR_USERNAME/claude-code-vision.git
cd claude-code-vision

# Install with pip
pip install -e .

# Or install from PyPI (when published)
pip install claude-code-vision
```

### Step 3: Initialize Configuration

```bash
# Generate default config file
claude-vision --init

# Config created at: ~/.config/claude-code-vision/config.yaml
```

### Step 4: Verify Installation

```bash
# Run diagnostic check
claude-vision --doctor

# Expected output:
# ✅ Claude Code found: /home/user/.claude/config.json
# ✅ OAuth token valid
# ✅ Desktop environment: X11
# ✅ Screenshot tool: scrot (installed)
# ✅ Area selection tool: xrectsel (installed)
# ✅ Python dependencies: OK
# 🎉 Claude Code Vision is ready!
```

---

## First Screenshot

### Test in Terminal

```bash
# Capture screenshot and analyze with Claude
claude-vision "What's on my screen?"

# Expected workflow:
# 1. Screenshot captured
# 2. Image optimized (<2MB)
# 3. Sent to Claude
# 4. Response printed in terminal
```

### Test in Claude Code Session

```bash
# Start Claude Code
claude

# In Claude Code, type:
/vision "Analyze the error message on my screen"

# Claude will respond with analysis based on screenshot
```

---

## Common Commands

### Full Screen Capture
```bash
/vision "What IDE am I using?"
/vision "Review my code layout"
/vision "What's the error in the terminal?"
```

### Area Selection
```bash
/vision.area "Analyze this specific error dialog"
# Graphical selection tool launches → drag to select region → analysis

# Or with coordinates (if you know them):
/vision.area --coords 100,200,800,600 "What's in this region?"
```

### Auto-Monitoring (Advanced)
```bash
# Start monitoring (captures every 30 seconds)
/vision.auto

# Work on your code...
# Screenshots captured silently in background

# Query Claude about changes:
"Has anything changed on screen since last check?"

# Stop monitoring
/vision.stop
```

---

## Privacy Setup (Recommended)

### Configure Privacy Zones

Edit `~/.config/claude-code-vision/config.yaml`:

```yaml
privacy:
  enabled: true
  zones:
    # Example: Hide password manager window (top-right corner)
    - name: "1password"
      x: 1500
      y: 0
      width: 420
      height: 100
      monitor: 0

    # Example: Hide notifications area
    - name: "notifications"
      x: 1600
      y: 0
      width: 320
      height: 80
```

### Find Zone Coordinates

```bash
# Launch screenshot with coordinates displayed
claude-vision --show-coords

# Click corners of sensitive area
# Coordinates printed: x=1500, y=0, width=420, height=100

# Add to config.yaml privacy.zones section
```

---

## Multi-Monitor Setup

### Detect Monitors

```bash
# List available monitors
claude-vision --list-monitors

# Output:
# Monitor 0 (primary): eDP-1 - 1920x1080
# Monitor 1: HDMI-1 - 2560x1440
```

### Set Default Monitor

Edit `~/.config/claude-code-vision/config.yaml`:

```yaml
monitors:
  default: 1  # Use second monitor by default
```

### Capture Specific Monitor

```bash
/vision --monitor 1 "Analyze my second screen"
```

---

## Troubleshooting

### "No display available" Error

**Problem**: Running in SSH session or headless environment.

**Solution**: Must run from graphical terminal (not SSH).

```bash
# Check if display available
echo $DISPLAY  # Should show: :0 or :1

# If empty, you're headless - switch to graphical session
```

### "Screenshot tool not found" Error

**Problem**: scrot/grim not installed.

**Solution**: Install system dependencies (see Installation Step 1).

```bash
# Check what's installed
which scrot grim import

# Install missing tools
sudo apt install scrot -y  # for X11
sudo apt install grim -y   # for Wayland
```

### "OAuth token expired" Error

**Problem**: Claude Code authentication expired.

**Solution**: Re-authenticate with Claude Code.

```bash
# Re-login to Claude Code
claude login

# Verify token valid
claude-vision --doctor
```

### "Payload too large" Error

**Problem**: Screenshot exceeds 2MB after optimization.

**Solution**: Adjust quality settings or reduce resolution.

Edit `~/.config/claude-code-vision/config.yaml`:

```yaml
screenshot:
  quality: 70  # Reduce from default 85
  max_size_mb: 1.5  # More aggressive optimization
```

### Screenshot Shows Wrong Monitor

**Problem**: Multi-monitor setup capturing wrong screen.

**Solution**: Specify monitor explicitly.

```bash
# Capture specific monitor
/vision --monitor 1 "Analyze this screen"

# Or set default in config
# monitors.default: 1
```

---

## Configuration Reference

### Minimal Config (Auto-Detect Everything)

`~/.config/claude-code-vision/config.yaml`:

```yaml
version: "1.0"

# Everything else uses defaults - no configuration needed!
```

### Recommended Config

```yaml
version: "1.0"

screenshot:
  quality: 85  # Good balance of quality/size
  max_size_mb: 2.0

privacy:
  enabled: true
  prompt_first_use: true
  zones: []  # Add your privacy zones here

monitoring:
  interval_seconds: 30
  max_duration_minutes: 30

logging:
  level: INFO  # Set to DEBUG for troubleshooting
```

### Power User Config

```yaml
version: "1.0"

screenshot:
  tool: scrot  # Force specific tool (instead of auto)
  format: webp  # Better compression than jpeg
  quality: 80
  max_size_mb: 1.5

monitors:
  default: 1  # Second monitor

area_selection:
  tool: slurp  # Force Wayland tool
  show_coordinates: true

privacy:
  enabled: true
  prompt_first_use: false  # Skip confirmation prompt
  zones:
    - name: "password_manager"
      x: 1500
      y: 0
      width: 420
      height: 100

monitoring:
  interval_seconds: 15  # Faster captures
  max_duration_minutes: 60  # Longer sessions
  idle_pause_minutes: 3  # Pause sooner
  change_detection: true

logging:
  level: DEBUG
  file: "~/.config/claude-code-vision/debug.log"
  max_size_mb: 50
```

---

## Use Cases

### 1. Debugging UI Issues

```bash
# Show Claude your broken UI
/vision "The submit button is not aligned correctly. What CSS should I fix?"
```

### 2. Code Review

```bash
# Share your IDE layout
/vision "Review the code structure in my editor. Any improvements?"
```

### 3. Error Analysis

```bash
# Capture error dialog
/vision.area "What does this error mean and how do I fix it?"
# → Select error dialog with mouse
```

### 4. Design Feedback

```bash
# Monitor design iterations
/vision.auto
# Make design changes...
# Ask Claude: "What changed since last screenshot? Looks better?"
/vision.stop
```

### 5. Documentation

```bash
# Capture terminal output
/vision "Document this command output in markdown format"
```

---

## Advanced Features

### Custom Slash Commands

Create `.claude/commands/vision-debug.md`:

```markdown
Capture screenshot and analyze for common bugs:
- UI alignment issues
- Console errors
- Broken layouts
- Missing elements

/vision "Perform detailed debugging analysis on this screen"
```

Usage: `/vision-debug`

### Scripting Integration

```python
#!/usr/bin/env python3
from claude_vision import VisionService
from claude_vision.config import load_config

config = load_config()
vision = VisionService(config)

# Capture and analyze programmatically
response = vision.execute_vision_command("Count how many terminal windows are open")
print(f"Claude says: {response}")
```

### CI/CD Integration

```yaml
# .github/workflows/screenshot-tests.yml
- name: Capture test failure screenshot
  if: failure()
  run: |
    export DISPLAY=:99
    Xvfb :99 -screen 0 1920x1080x24 &
    claude-vision "Analyze test failure screen" > failure-report.txt
```

---

## Next Steps

1. **Read Full Documentation**: `docs/README.md`
2. **Configure Privacy Zones**: Protect sensitive information
3. **Try Area Selection**: Master `/vision.area` for focused captures
4. **Experiment with Auto-Mode**: Use `/vision.auto` for iterative work
5. **Join Community**: Share use cases and get help

---

## Getting Help

### Documentation
- Full docs: `docs/`
- API reference: `docs/api.md`
- Examples: `examples/`

### Community
- GitHub Issues: Report bugs and feature requests
- Discussions: Share use cases and ask questions

### Diagnostics

```bash
# Full system diagnostic
claude-vision --doctor --verbose

# Test screenshot capture
claude-vision --test-capture

# Validate configuration
claude-vision --validate-config

# View logs
tail -f ~/.config/claude-code-vision/vision.log
```

---

**You're ready to go!** Start with `/vision "Hello!"` and see Claude analyze your screen.
