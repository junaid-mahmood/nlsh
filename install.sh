set -e

INSTALL_DIR="$HOME/.nlsh"
REPO_URL="https://github.com/junaid-mahmood/nlsh.git"

echo "Installing nlsh..."

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required. Please install it first."
    exit 1
fi

if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull --quiet
else
    echo "Downloading nlsh..."
    git clone --quiet "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "Creating nlsh command..."
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/nlsh" << 'EOF'
#!/bin/bash
source "$HOME/.nlsh/venv/bin/activate"
python "$HOME/.nlsh/nlsh.py" "$@"
EOF
chmod +x "$HOME/.local/bin/nlsh"

setup_shell() {
    local rc_file="$1"
    touch "$rc_file"
    
    if ! grep -q '.local/bin' "$rc_file" 2>/dev/null; then
        echo '' >> "$rc_file"
        echo '# nlsh - PATH' >> "$rc_file"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc_file"
    fi
    
    if ! grep -q 'nlsh # auto-start' "$rc_file" 2>/dev/null; then
        echo '' >> "$rc_file"
        echo '# nlsh - auto-start (remove this line to disable)' >> "$rc_file"
        echo '[ -t 0 ] && [ -x "$HOME/.local/bin/nlsh" ] && nlsh # auto-start' >> "$rc_file"
        echo "Added nlsh auto-start to $rc_file"
    fi
}

setup_shell "$HOME/.zprofile"
setup_shell "$HOME/.zshrc"
setup_shell "$HOME/.bashrc"
setup_shell "$HOME/.bash_profile"

export PATH="$HOME/.local/bin:$PATH"

echo ""
echo "nlsh installed successfully!"
echo ""
echo "Open a new terminal to start using nlsh, or run: nlsh"
echo ""
