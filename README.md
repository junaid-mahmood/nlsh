# nlsh - Natural Language Shell

Talk to your terminal in plain English.

> **Requirements**: macOS, Linux, or Windows (PowerShell)

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

```bash
curl -fsSL https://raw.githubusercontent.com/junaid-mahmood/nlsh/main/uninstall.sh | bash
```

## Usage

```bash
nlsh
```

Type naturally:
- `list all python files` → `find . -name "*.py"`
- `git commit with message fixed bug` → `git commit -m "fixed bug"`

Commands:
- `!api` - Change API key
- `!help` - Show help
- `!cmd` - Run cmd directly
- `Ctrl+D` - Exit
