#!/usr/bin/env python3
import signal
import os
import sys
import subprocess
import readline
import re

# Dangerous command patterns that require explicit confirmation
DANGEROUS_PATTERNS = [
    r'\brm\s+(-[rf]+\s+)*[/~]',           # rm with / or ~ paths
    r'\brm\s+-[rf]*\s*\*',                 # rm -rf *
    r'\bsudo\b',                           # sudo commands
    r'\bchmod\s+777\b',                    # chmod 777
    r'\b>\s*/dev/',                        # redirect to /dev/
    r'\bmkfs\b',                           # filesystem format
    r'\bdd\b.*\bof=',                      # dd write operations
    r':(){.*};:',                          # fork bomb
    r'\bkill\s+-9\s+-1\b',                 # kill all processes
]

def is_dangerous_command(cmd: str) -> bool:
    """Check if command matches known dangerous patterns."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False

def exit_handler(sig, frame):
    print()
    raise InterruptedError()

signal.signal(signal.SIGINT, exit_handler)

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")

def load_env():
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value

def save_api_key(api_key: str):
    """Save API key with restricted file permissions."""
    with open(env_path, "w") as f:
        f.write(f"GEMINI_API_KEY={api_key}\n")
    # Set file permissions to owner-only read/write (600)
    os.chmod(env_path, 0o600)

def setup_api_key():
    print(f"\n\033[36mGet your free key at: https://aistudio.google.com/apikey\033[0m\n")
    api_key = input("\033[33mEnter your Gemini API key:\033[0m ").strip()
    if not api_key:
        print("No API key provided.")
        sys.exit(1)
    save_api_key(api_key)
    os.environ["GEMINI_API_KEY"] = api_key
    print("\033[32m✓ API key saved!\033[0m\n")

def show_help():
    print("\033[36m!api\033[0m       - Change API key")
    print("\033[36m!uninstall\033[0m - Remove nlsh")
    print("\033[36m!help\033[0m      - Show this help")
    print("\033[36m!cmd\033[0m       - Run cmd directly (requires confirmation)")
    print("\033[36mexit\033[0m       - Exit nlsh")
    print("\033[36m--version\033[0m  - Show version")
    print("\033[36m--help\033[0m     - Show this help")
    print()

VERSION = "1.1.0"

def show_version():
    print(f"nlsh version {VERSION}")

# Handle --help and --version BEFORE any API key setup
if len(sys.argv) > 1:
    arg = sys.argv[1]
    if arg in ("--help", "-h"):
        show_help()
        sys.exit(0)
    if arg in ("--version", "-v"):
        show_version()
        sys.exit(0)

load_env()

first_run = not os.getenv("GEMINI_API_KEY")
if first_run:
    setup_api_key()
    print("\033[1mnlsh\033[0m - talk to your terminal\n")
    show_help()

from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

command_history = []
MAX_HISTORY = 10
MAX_CONTEXT_CHARS = 4000

def get_context_size() -> int:
    return sum(len(e["command"]) + len(e["output"]) for e in command_history)

def add_to_history(command: str, output: str = ""):
    command_history.append({
        "command": command,
        "output": output[:500] if output else ""
    })
    while len(command_history) > MAX_HISTORY:
        command_history.pop(0)
    while get_context_size() > MAX_CONTEXT_CHARS and len(command_history) > 1:
        command_history.pop(0)

def format_history() -> str:
    if not command_history:
        return "No previous commands."

    lines = []
    for i, entry in enumerate(command_history[-5:], 1):
        lines.append(f"{i}. $ {entry['command']}")
        if entry['output']:
            output_lines = entry['output'].strip().split('\n')[:2]
            for line in output_lines:
                lines.append(f"   {line}")
    return "\n".join(lines)

def get_command(user_input: str, cwd: str) -> str:
    history_context = format_history()
    prompt = f"""You are a shell command translator. Convert the user's request into a shell command for macOS/zsh.
Current directory: {cwd}

Recent command history:
{history_context}

Rules:
- Output ONLY the command, nothing else
- No explanations, no markdown, no backticks
- If unclear, make a reasonable assumption
- Prefer simple, common commands
- Use the command history for context (e.g., "do that again", "delete the file I just created")
- NEVER use rm -rf on home directory, root, or with wildcards unless explicitly requested
- Prefer safe alternatives (trash over rm, git stash over reset --hard)

User request: {user_input}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()

def is_natural_language(text: str) -> bool:
    if text.startswith("!"):
        return False
    shell_commands = ["ls", "pwd", "clear", "exit", "quit", "whoami", "date", "cal",
                      "top", "htop", "history", "which", "man", "touch", "head", "tail",
                      "grep", "find", "sort", "wc", "diff", "tar", "zip", "unzip"]
    shell_starters = ["cd ", "ls ", "echo ", "cat ", "mkdir ", "rm ", "cp ", "mv ",
                      "git ", "npm ", "node ", "npx ", "python", "pip ", "brew ", "curl ",
                      "wget ", "chmod ", "chown ", "sudo ", "vi ", "vim ", "nano ", "code ",
                      "open ", "export ", "source ", "docker ", "kubectl ", "aws ", "gcloud ",
                      "./", "/", "~", "$", ">", ">>", "|", "&&"]
    if text in shell_commands:
        return False
    return not any(text.startswith(s) for s in shell_starters)

def confirm_dangerous_command(cmd: str) -> bool:
    """Require explicit 'yes' confirmation for dangerous commands."""
    print(f"\033[31m⚠️  WARNING: This command may be dangerous!\033[0m")
    print(f"\033[33m→ {cmd}\033[0m")
    confirm = input("\033[31mType 'yes' to execute, anything else to cancel:\033[0m ").strip()
    return confirm.lower() == "yes"

def execute_command(cmd: str, require_confirm: bool = True) -> None:
    """Execute a shell command with optional confirmation for dangerous commands."""
    if is_dangerous_command(cmd):
        if not confirm_dangerous_command(cmd):
            print("Command cancelled.")
            return

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    add_to_history(cmd, result.stdout + result.stderr)

def main():
    while True:
        try:
            cwd = os.getcwd()
            prompt = f"\033[32m{os.path.basename(cwd)}\033[0m > "
            user_input = input(prompt).strip()

            if not user_input:
                continue

            # Exit command
            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            if user_input.startswith("cd "):
                path = os.path.expanduser(user_input[3:].strip())
                try:
                    os.chdir(path)
                except Exception as e:
                    print(f"cd: {e}")
                continue
            elif user_input == "cd":
                os.chdir(os.path.expanduser("~"))
                continue

            if user_input == "!api":
                setup_api_key()
                global client
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                continue

            if user_input == "!uninstall":
                confirm = input("\033[33mRemove nlsh? [y/N]\033[0m ")
                if confirm.lower() == "y":
                    import shutil
                    install_dir = os.path.expanduser("~/.nlsh")
                    bin_path = os.path.expanduser("~/.local/bin/nlsh")
                    if os.path.exists(install_dir):
                        shutil.rmtree(install_dir)
                    if os.path.exists(bin_path):
                        os.remove(bin_path)
                    print("\033[32m✓ nlsh uninstalled\033[0m")
                    print("Note: You may want to remove the PATH line from your shell rc file.")
                    sys.exit(0)
                continue

            if user_input == "!help":
                show_help()
                continue

            # Raw command execution with ! prefix - now requires confirmation for dangerous commands
            if user_input.startswith("!"):
                cmd = user_input[1:]
                if not cmd:
                    continue
                execute_command(cmd)
                continue

            if not is_natural_language(user_input):
                execute_command(user_input)
                continue

            command = get_command(user_input, cwd)

            # Check for dangerous AI-generated commands
            if is_dangerous_command(command):
                if not confirm_dangerous_command(command):
                    print("Command cancelled.")
                    continue
                # Already confirmed, execute directly
                if command.startswith("cd "):
                    path = os.path.expanduser(command[3:].strip())
                    try:
                        os.chdir(path)
                    except Exception as e:
                        print(f"cd: {e}")
                else:
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    print(result.stdout, end="")
                    if result.stderr:
                        print(result.stderr, end="")
                    add_to_history(command, result.stdout + result.stderr)
            else:
                # Normal confirmation flow
                confirm = input(f"\033[33m→ {command}\033[0m [Enter/n] ")

                if confirm.lower() not in ("n", "no"):
                    if command.startswith("cd "):
                        path = os.path.expanduser(command[3:].strip())
                        try:
                            os.chdir(path)
                        except Exception as e:
                            print(f"cd: {e}")
                    else:
                        result = subprocess.run(command, shell=True, capture_output=True, text=True)
                        print(result.stdout, end="")
                        if result.stderr:
                            print(result.stderr, end="")
                        add_to_history(command, result.stdout + result.stderr)

        except (EOFError, InterruptedError, KeyboardInterrupt):
            continue
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                print("\033[31mrate limit hit - wait a moment and try again\033[0m")
            elif "InterruptedError" not in err and "KeyboardInterrupt" not in err:
                print(f"\033[31merror: {err[:100]}\033[0m")

if __name__ == "__main__":
    main()
