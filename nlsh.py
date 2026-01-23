#!/usr/bin/env python3
import signal
import os
import sys
import subprocess
import shutil
try:
    import readline
except ImportError:
    readline = None


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
    with open(env_path, "w") as f:
        f.write(f"GEMINI_API_KEY={api_key}\n")

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
    print("\033[36m!cmd\033[0m       - Run cmd directly")
    print()

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

def get_shell() -> str:
    if sys.platform == "win32":
        return "Windows/PowerShell"
    return "macOS/zsh"

def get_shell_executable():
    if sys.platform != "win32":
        return None
    return "pwsh" if shutil.which("pwsh") else "powershell"

def get_command(user_input: str, cwd: str) -> str:
    history_context = format_history()
    shell_info = get_shell()
    prompt = f"""You are a shell command translator. Convert the user's request into a shell command for {shell_info}.
Current directory: {cwd}

Recent command history:
{history_context}

Rules:
- Output ONLY the command, nothing else
- No explanations, no markdown, no backticks
- If unclear, make a reasonable assumption
- Prefer simple, common commands
- Use the command history for context (e.g., "do that again", "delete the file I just created")

User request: {user_input}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        err_msg = str(e)
        if "API key" in err_msg or "INVALID_ARGUMENT" in err_msg:
            print("\033[31m✕ Invalid API key provided.\033[0m")
            setup_api_key()
            global client
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            return get_command(user_input, cwd)
        raise e

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
                      "dir ", "Get-", "Set-", "New-", "Remove-", "Invoke-",
                      "./", "/", "~", "$", ">", ">>", "|", "&&"]
    if text in shell_commands:
        return False
    return not any(text.startswith(s) for s in shell_starters)

def main():
    # Handle single command execution via CLI arguments
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:]).strip()
        if user_input:
            process_input(user_input)
            return

    while True:
        try:
            cwd = os.getcwd()
            prompt = f"\033[32m{os.path.basename(cwd)}\033[0m > "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            process_input(user_input)
            
        except EOFError:
            print()
            sys.exit(0)
        except (InterruptedError, KeyboardInterrupt):
            print()
            continue
        except Exception as e:
            handle_exception(e)

def process_input(user_input: str):
    cwd = os.getcwd()

    if user_input in ["exit", "exit()", "quit", "quit()"]:
        sys.exit(0)
    
    if user_input.startswith("cd "):
        path = os.path.expanduser(user_input[3:].strip())
        try:
            os.chdir(path)
        except Exception as e:
            print(f"cd: {e}")
        return
    elif user_input == "cd":
        os.chdir(os.path.expanduser("~"))
        return
    
    if user_input == "!api":
        setup_api_key()
        global client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        return
    
    if user_input == "!uninstall":
        confirm = input("\033[33mRemove nlsh? [y/N]\033[0m ")
        if confirm.lower() == "y":
            install_dir = os.path.expanduser("~/.nlsh")
            if sys.platform == "win32":
                # Cleanup for Windows
                if os.path.exists(install_dir):
                    shutil.rmtree(install_dir)
                print("\033[32m✓ nlsh uninstalled\033[0m")
                print("\033[33mNote: You may still have nlsh in your PATH or PowerShell Profile.\033[0m")
            else:
                bin_path = os.path.expanduser("~/.local/bin/nlsh")
                if os.path.exists(install_dir):
                    shutil.rmtree(install_dir)
                if os.path.exists(bin_path):
                    os.remove(bin_path)
                print("\033[32m✓ nlsh uninstalled\033[0m")
            sys.exit(0)
        return
    
    if user_input == "!help":
        show_help()
        return
    
    if user_input.startswith("!"):
        cmd = user_input[1:]
        if not cmd:
            return
        shell_executable = get_shell_executable()
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable=shell_executable)
        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="")
        add_to_history(cmd, result.stdout + result.stderr)
        return
    
    if not is_natural_language(user_input):
        shell_executable = get_shell_executable()
        result = subprocess.run(user_input, shell=True, capture_output=True, text=True, executable=shell_executable)
        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="")
        add_to_history(user_input, result.stdout + result.stderr)
        return
    
    command = get_command(user_input, cwd)
    confirm = input(f"\033[33m→ {command}\033[0m [Enter] ")
    
    if confirm == "":
        if command.startswith("cd "):
            path = os.path.expanduser(command[3:].strip())
            try:
                os.chdir(path)
            except Exception as e:
                print(f"cd: {e}")
        else:
            shell_executable = get_shell_executable()
            result = subprocess.run(command, shell=True, capture_output=True, text=True, executable=shell_executable)
            print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="")
            add_to_history(command, result.stdout + result.stderr)

def handle_exception(e: Exception):
    err = str(e)
    # Handle API Key issues specifically
    if "API key" in err or "INVALID_ARGUMENT" in err:
        print("\033[31m✕ Invalid API key. Please check your key and try again.\033[0m")
        setup_api_key()
        global client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    # Handle Rate Limits
    elif "429" in err or "quota" in err.lower():
        print("\033[31m✕ Rate limit hit - wait a moment and try again.\033[0m")
    # Handle other generic errors cleanly
    else:
        # Try to extract the message from the error object if it's a common SDK error
        clean_msg = err
        if "message" in err and ":" in err:
            try:
                # Often SDK errors are like "Code: Message"
                clean_msg = err.split(":", 1)[1].strip()
                if "{" in clean_msg: # If it's still a JSON blob, just take the first part
                    clean_msg = clean_msg.split("{", 1)[0].strip()
            except:
                pass
        
        print(f"\033[31m✕ Error: {clean_msg}\033[0m")

if __name__ == "__main__":
    main()
