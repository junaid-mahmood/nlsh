echo "Uninstalling nlsh..."

rm -rf "$HOME/.nlsh"
rm -f "$HOME/.local/bin/nlsh"

# Remove auto-start lines from shell configs
for rc_file in "$HOME/.zprofile" "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile"; do
    if [ -f "$rc_file" ]; then
        # Remove nlsh auto-start line
        sed -i '' '/nlsh # auto-start/d' "$rc_file" 2>/dev/null || sed -i '/nlsh # auto-start/d' "$rc_file" 2>/dev/null
        sed -i '' '/nlsh - auto-start/d' "$rc_file" 2>/dev/null || sed -i '/nlsh - auto-start/d' "$rc_file" 2>/dev/null
    fi
done

echo "✓ nlsh has been removed"
