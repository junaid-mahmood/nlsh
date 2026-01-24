#!/bin/bash
set -euo pipefail

INSTALL_DIR="$HOME/.nlsh"
REPO_URL="https://github.com/junaid-mahmood/nlsh.git"

echo "Installing nlsh..."

# Check dependencies
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required. Please install it first."
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "Git is required. Please install it first."
    exit 1
fi

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull --quiet
else
    echo "Downloading nlsh..."
    git clone --quiet "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Setup Python virtual environment
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Create launcher script
echo "Creating nlsh command..."
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/nlsh" << 'EOF'
#!/bin/bash
source "$HOME/.nlsh/venv/bin/activate"
python "$HOME/.nlsh/nlsh.py" "$@"
EOF
chmod +x "$HOME/.local/bin/nlsh"

# Only add PATH if not already present - touch only ONE rc file based on current shell
setup_path() {
    local rc_file="$1"

    if [ ! -f "$rc_file" ]; then
        return
    fi

    if ! grep -q '.local/bin' "$rc_file" 2>/dev/null; then
        echo '' >> "$rc_file"
        echo '# nlsh - PATH' >> "$rc_file"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc_file"
        echo "Added PATH to $rc_file"
    fi
}

# Detect current shell and only modify the relevant rc file
case "$SHELL" in
    */zsh)
        setup_path "$HOME/.zshrc"
        ;;
    */bash)
        # On macOS, .bash_profile is used for login shells
        if [[ "$(uname)" == "Darwin" ]]; then
            setup_path "$HOME/.bash_profile"
        else
            setup_path "$HOME/.bashrc"
        fi
        ;;
    *)
        # Fallback: try common rc files
        setup_path "$HOME/.profile"
        ;;
esac

export PATH="$HOME/.local/bin:$PATH"

echo ""
echo "nlsh installed successfully!"
echo ""
echo "To start using nlsh:"
echo "  1. Open a new terminal, or run: export PATH=\"\$HOME/.local/bin:\$PATH\""
echo "  2. Run: nlsh"
echo ""
echo "Note: nlsh does NOT auto-start. Run 'nlsh' when you want to use it."
echo ""
