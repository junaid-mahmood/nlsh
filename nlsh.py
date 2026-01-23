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

def verify_api_key():
    global client
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        setup_api_key()
        api_key = os.getenv("GEMINI_API_KEY")
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        client.models.list(config={'page_size': 1})
        return True
    except Exception as e:
        err_msg = str(e)
        if any(x in err_msg for x in ["API key", "INVALID_ARGUMENT", "401"]):
            print("\033[31m✕ Invalid API key detected.\033[0m")
            setup_api_key()
            return verify_api_key()
        else:
            print(f"\033[31m✕ Connection error: {err_msg[:100]}\033[0m")
            return False

load_env()
verify_api_key()

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
    while len(command_history) > MAX_HISTORY or get_context_size() > MAX_CONTEXT_CHARS:
        if len(command_history) <= 1: break
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

def get_shell_executable():
    if sys.platform != "win32":
        return None
    return shutil.which("pwsh") or shutil.which("powershell")

def run_shell_command(command: str, capture_output: bool = True):
    exe = get_shell_executable()
    if sys.platform == "win32" and exe:
        return subprocess.run([exe, "-NoProfile", "-Command", command], capture_output=capture_output, text=True)
    return subprocess.run(command, shell=True, capture_output=capture_output, text=True)

def get_command(user_input: str, cwd: str) -> str:
    global client
    shell_type = "Windows/PowerShell" if sys.platform == "win32" else "macOS/zsh"
    prompt = f"""You are a shell command translator. Convert the user's request into a shell command for {shell_type}.
Current directory: {cwd}

Recent command history:
{format_history()}

Rules:
- Output ONLY the command, nothing else
- No explanations, no markdown, no backticks
- If unclear, make a reasonable assumption
- Prefer simple, common commands
- Use context for follow-up requests (e.g. "do that again")

User request: {user_input}"""

    models = ["gemini-2.5-flash", "gemini-3-flash", "gemma-3-1b"]
    for model_name in models:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            return response.text.strip()
        except Exception as e:
            err = str(e)
            if any(x in err for x in ["API key", "INVALID_ARGUMENT"]):
                print("\033[31m✕ Invalid API key provided.\033[0m")
                setup_api_key()
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                return get_command(user_input, cwd)
            if any(x in err or x in err.lower() for x in ["429", "404", "quota", "not found"]):
                continue
            if model_name == models[-1]: raise e
    return "error: all models exhausted"

def is_natural_language(text: str) -> bool:
    if text.startswith("!"): return False
    cmds = ["ls", "pwd", "clear", "exit", "quit", "whoami", "date", "cal", "top", "htop", "history", "which", "man", "touch", "head", "tail", "grep", "find", "sort", "wc", "diff", "tar", "zip", "unzip"]
    starts = ["cd ", "ls ", "echo ", "cat ", "mkdir ", "rm ", "cp ", "mv ", "git ", "npm ", "node ", "npx ", "python", "pip ", "brew ", "curl ", "wget ", "chmod ", "chown ", "sudo ", "vi ", "vim ", "nano ", "code ", "open ", "export ", "source ", "docker ", "kubectl ", "aws ", "gcloud ", "dir ", "Get-", "Set-", "New-", "Remove-", "Invoke-", "./", "/", "~", "$", ">", ">>", "|", "&&"]
    return text not in cmds and not any(text.startswith(s) for s in starts)

def main():
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:]).strip()
        if cmd: process_input(cmd)
        return

    while True:
        try:
            cwd = os.getcwd()
            user_input = input(f"\033[32m{os.path.basename(cwd)}\033[0m > ").strip()
            if user_input: process_input(user_input)
        except EOFError:
            print(); sys.exit(0)
        except (InterruptedError, KeyboardInterrupt):
            print(); continue
        except Exception as e:
            handle_exception(e)

def process_input(inp: str):
    if inp in ["exit", "exit()", "quit", "quit()"]: sys.exit(0)
    
    if inp.startswith("cd ") or inp == "cd":
        path = os.path.expanduser(inp[3:].strip()) if inp.startswith("cd ") else "~"
        try: os.chdir(os.path.expanduser(path))
        except Exception as e: print(f"cd: {e}")
        return
    
    if inp == "!api":
        setup_api_key(); global client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        return
    
    if inp == "!uninstall":
        if input("\033[33mRemove nlsh? [y/N]\033[0m ").lower() == "y":
            shutil.rmtree(os.path.expanduser("~/.nlsh"), ignore_errors=True)
            if sys.platform != "win32":
                bin_p = os.path.expanduser("~/.local/bin/nlsh")
                if os.path.exists(bin_p): os.remove(bin_p)
            print("\033[32m✓ nlsh uninstalled\033[0m")
            sys.exit(0)
        return
    
    if inp == "!help": show_help(); return
    
    if inp.startswith("!") or not is_natural_language(inp):
        cmd = inp[1:] if inp.startswith("!") else inp
        res = run_shell_command(cmd)
        print(res.stdout, end=""); print(res.stderr, end="")
        add_to_history(cmd, res.stdout + res.stderr)
        return
    
    cmd = get_command(inp, os.getcwd())
    if input(f"\033[33m→ {cmd}\033[0m [Enter] ") == "":
        if cmd.startswith("cd "):
            try: os.chdir(os.path.expanduser(cmd[3:].strip()))
            except Exception as e: print(f"cd: {e}")
        else:
            res = run_shell_command(cmd)
            print(res.stdout, end=""); print(res.stderr, end="")
            add_to_history(cmd, res.stdout + res.stderr)

def handle_exception(e: Exception):
    global client
    err = str(e)
    if any(x in err for x in ["API key", "INVALID_ARGUMENT"]):
        print("\033[31m✕ Invalid API key. Please re-enter.\033[0m")
        setup_api_key()
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    elif "429" in err or "quota" in err.lower():
        print("\033[31m✕ Rate limit hit - try again in a moment.\033[0m")
    else:
        msg = err.split(":", 1)[1].strip() if ":" in err else err
        if "{" in msg: msg = msg.split("{", 1)[0].strip()
        print(f"\033[31m✕ Error: {msg}\033[0m")

if __name__ == "__main__":
    main()
