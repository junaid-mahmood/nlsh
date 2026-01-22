# nlsh - Natural Language Shell

Talk to your terminal in plain English.

> **Requirements**: Python 3.8+ and Git

## Install

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/junaid-mahmood/nlsh/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/junaid-mahmood/nlsh/main/install.ps1 | iex
```

## Uninstall

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/junaid-mahmood/nlsh/main/uninstall.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/junaid-mahmood/nlsh/main/uninstall.ps1 | iex
```

## Usage

```bash
nlsh
```

Type naturally:
- `list all python files` → `find . -name "*.py"` (Unix) / `dir /s *.py` (Windows)
- `git commit with message fixed bug` → `git commit -m "fixed bug"`

Commands:
- `!api` - Change API key
- `!help` - Show help
- `!cmd` - Run cmd directly
- `Ctrl+D` - Exit
