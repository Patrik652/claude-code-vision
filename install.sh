#!/bin/bash
#
# Claude Code Vision Installation Script
#
# This script installs Claude Code Vision and its dependencies.
# Supports: Ubuntu/Debian, Fedora/RHEL, Arch Linux
#
# Usage: ./install.sh [--dev]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Installation mode
DEV_MODE=false
if [[ "$1" == "--dev" ]]; then
    DEV_MODE=true
fi

# Print functions
print_header() {
    echo -e "${CYAN}=================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}=================================================${NC}"
}

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Detect OS and package manager
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        print_error "Cannot detect OS. /etc/os-release not found."
        exit 1
    fi

    case $OS in
        ubuntu|debian|pop)
            PKG_MANAGER="apt"
            ;;
        fedora|rhel|centos)
            PKG_MANAGER="dnf"
            ;;
        arch|manjaro)
            PKG_MANAGER="pacman"
            ;;
        *)
            print_warning "Unsupported OS: $OS. Attempting to continue..."
            PKG_MANAGER="unknown"
            ;;
    esac
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. This is not recommended for development installations."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check Python version
check_python() {
    print_step "Checking Python version..."

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

        if [[ $PYTHON_MAJOR -ge 3 && $PYTHON_MINOR -ge 8 ]]; then
            print_success "Python $PYTHON_VERSION detected"
            return 0
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            return 1
        fi
    else
        print_error "Python 3 not found"
        return 1
    fi
}

# Install system dependencies
install_system_deps() {
    print_step "Installing system dependencies..."

    case $PKG_MANAGER in
        apt)
            sudo apt update
            sudo apt install -y python3-pip python3-venv python3-dev

            # Detect desktop environment
            if [ -n "$WAYLAND_DISPLAY" ]; then
                print_step "Wayland detected, installing grim and slurp..."
                sudo apt install -y grim slurp wlr-randr
            elif [ -n "$DISPLAY" ]; then
                print_step "X11 detected, installing scrot and slop..."
                sudo apt install -y scrot slop xdotool
            else
                print_warning "No display detected. Installing both X11 and Wayland tools..."
                sudo apt install -y scrot slop grim slurp
            fi

            # Optional: ImageMagick for fallback
            sudo apt install -y imagemagick
            ;;

        dnf)
            sudo dnf install -y python3-pip python3-devel

            if [ -n "$WAYLAND_DISPLAY" ]; then
                sudo dnf install -y grim slurp wlr-randr
            elif [ -n "$DISPLAY" ]; then
                sudo dnf install -y scrot slop xdotool
            else
                sudo dnf install -y scrot slop grim slurp
            fi

            sudo dnf install -y ImageMagick
            ;;

        pacman)
            sudo pacman -Sy --noconfirm python-pip

            if [ -n "$WAYLAND_DISPLAY" ]; then
                sudo pacman -S --noconfirm grim slurp wlr-randr
            elif [ -n "$DISPLAY" ]; then
                sudo pacman -S --noconfirm scrot slop xdotool
            else
                sudo pacman -S --noconfirm scrot slop grim slurp
            fi

            sudo pacman -S --noconfirm imagemagick
            ;;

        *)
            print_warning "Unknown package manager. Please install dependencies manually:"
            echo "  - Python 3.8+"
            echo "  - pip"
            echo "  - Screenshot tool: scrot (X11) or grim (Wayland)"
            echo "  - Region selector: slop (X11) or slurp (Wayland)"
            ;;
    esac

    print_success "System dependencies installed"
}

# Create virtual environment
create_venv() {
    print_step "Creating Python virtual environment..."

    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Skipping..."
    else
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
}

# Install Python dependencies
install_python_deps() {
    print_step "Installing Python dependencies..."

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        # Fallback: install core dependencies
        pip install click pyyaml pillow requests
    fi

    if [ "$DEV_MODE" = true ]; then
        print_step "Installing development dependencies..."
        if [ -f "requirements-dev.txt" ]; then
            pip install -r requirements-dev.txt
        else
            pip install pytest pytest-cov mypy black ruff
        fi
    fi

    # Install package in editable mode
    if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        pip install -e .
    fi

    print_success "Python dependencies installed"
}

# Create configuration
create_config() {
    print_step "Initializing configuration..."

    # Activate venv
    source venv/bin/activate

    # Run init command
    if command -v claude-vision &> /dev/null; then
        claude-vision --init || print_warning "Config already exists"
        print_success "Configuration initialized"
    else
        print_warning "claude-vision command not available yet. Run 'source venv/bin/activate' and 'claude-vision --init' manually."
    fi
}

# Run diagnostics
run_diagnostics() {
    print_step "Running diagnostics..."

    source venv/bin/activate

    if command -v claude-vision &> /dev/null; then
        claude-vision --doctor
    else
        print_warning "claude-vision command not available. Skipping diagnostics."
    fi
}

# Main installation
main() {
    print_header "Claude Code Vision Installation"

    # Check if we should run as regular user
    check_root

    # Detect operating system
    print_step "Detecting operating system..."
    detect_os
    print_success "Detected: $OS ($PKG_MANAGER)"

    # Check Python
    if ! check_python; then
        print_error "Python 3.8+ is required. Please install it first."
        exit 1
    fi

    # Install system dependencies
    install_system_deps

    # Create virtual environment
    create_venv

    # Install Python dependencies
    install_python_deps

    # Create configuration
    create_config

    # Print summary
    echo ""
    print_header "Installation Complete!"
    echo ""
    echo -e "${GREEN}✓ Claude Code Vision is installed${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "  1. Activate virtual environment:"
    echo -e "     ${YELLOW}source venv/bin/activate${NC}"
    echo ""
    echo -e "  2. Run diagnostics:"
    echo -e "     ${YELLOW}claude-vision --doctor${NC}"
    echo ""
    echo -e "  3. Test screenshot capture:"
    echo -e "     ${YELLOW}claude-vision --test-capture${NC}"
    echo ""
    echo -e "  4. Try your first command (from within Claude Code):"
    echo -e "     ${YELLOW}/vision \"What do you see?\"${NC}"
    echo ""

    if [ "$DEV_MODE" = true ]; then
        echo -e "${CYAN}Development mode enabled${NC}"
        echo -e "  • Run tests: ${YELLOW}pytest${NC}"
        echo -e "  • Type checking: ${YELLOW}mypy src${NC}"
        echo -e "  • Format code: ${YELLOW}black src${NC}"
        echo ""
    fi

    print_header "Installation Summary"
    echo -e "  OS: ${GREEN}$OS${NC}"
    echo -e "  Package Manager: ${GREEN}$PKG_MANAGER${NC}"
    echo -e "  Python: ${GREEN}$(python3 --version)${NC}"
    echo -e "  Display: ${GREEN}${DISPLAY:-${WAYLAND_DISPLAY:-Not detected}}${NC}"
    echo ""

    # Run diagnostics
    echo -e "${CYAN}Running diagnostics...${NC}"
    echo ""
    run_diagnostics
}

# Run main installation
main
