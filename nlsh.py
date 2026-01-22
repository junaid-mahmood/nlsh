#!/usr/bin/env python3
import signal
import os
import sys
import subprocess
import readline


def exit_handler(sig, frame):
    print()
    raise InterruptedError()


signal.signal(signal.SIGINT, exit_handler)

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")

# Provider configurations - Gemini remains default, Z.AI is optional
PROVIDERS = {
    "gemini": {
        "name": "Gemini",
        "env_key": "GEMINI_API_KEY",
        "api_url": "https://aistudio.google.com/apikey",
        "default_model": "gemini-2.5-flash",
        "models": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
    },
    "zai": {
        "name": "Z.AI",
        "env_key": "ZAI_API_KEY",
        "base_url": "https://api.z.ai/api/coding/paas/v4",
        "api_url": "https://z.ai",
        "default_model": "glm-4.7",
        "models": ["glm-4.7", "glm-4.6", "glm-4.5", "glm-4.5-flash"],
    },
}

# Current provider/model state (defaults to gemini)
current_provider = "gemini"
current_model = None  # Will use provider's default if None


def load_env():
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


def save_api_key(api_key: str, provider: str = "gemini"):
    """Save API key while preserving other keys in .env"""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value

    env_key = PROVIDERS[provider]["env_key"]
    env_vars[env_key] = api_key

    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")


def setup_api_key(provider: str = "gemini", exit_on_empty: bool = True):
    """Setup API key for a provider"""
    cfg = PROVIDERS[provider]
    print(f"\n\033[36mGet your {cfg['name']} key at: {cfg['api_url']}\033[0m\n")
    api_key = input(f"\033[33mEnter your {cfg['name']} API key:\033[0m ").strip()
    if not api_key:
        if exit_on_empty:
            print("No API key provided.")
            sys.exit(1)
        return False
    save_api_key(api_key, provider)
    os.environ[cfg["env_key"]] = api_key
    print("\033[32m✓ API key saved!\033[0m\n")
    return True


def show_help():
    print("\033[36m!api\033[0m        - Change API key for current provider")
    print("\033[36m!provider\033[0m   - Switch provider (gemini/zai/zhipu)")
    print("\033[36m!providers\033[0m  - List available providers")
    print("\033[36m!model\033[0m      - Switch model")
    print("\033[36m!models\033[0m     - List available models")
    print("\033[36m!uninstall\033[0m  - Remove nlsh")
    print("\033[36m!help\033[0m       - Show this help")
    print("\033[36m!cmd\033[0m        - Run cmd directly")
    print()


load_env()


# Determine which provider to use based on available API keys
def detect_provider():
    """Detect which provider has an API key configured"""
    for pid in ["gemini", "zai"]:
        if os.getenv(PROVIDERS[pid]["env_key"]):
            return pid
    return "gemini"  # Default to gemini


current_provider = detect_provider()

first_run = not os.getenv(PROVIDERS[current_provider]["env_key"])
if first_run:
    setup_api_key(current_provider)
    print("\033[1mnlsh\033[0m - talk to your terminal\n")
    show_help()

# Client management - lazy loading for non-gemini providers
gemini_client = None
openai_client = None


def get_gemini_client():
    global gemini_client
    if gemini_client is None:
        from google import genai

        gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return gemini_client


def get_openai_client(provider: str):
    global openai_client
    cfg = PROVIDERS[provider]
    # Recreate client if provider changed (different base_url)
    from openai import OpenAI

    openai_client = OpenAI(api_key=os.getenv(cfg["env_key"]), base_url=cfg["base_url"])
    return openai_client


# Initialize default client (gemini)
if current_provider == "gemini":
    client = get_gemini_client()
else:
    client = get_openai_client(current_provider)

command_history = []
MAX_HISTORY = 10
MAX_CONTEXT_CHARS = 4000


def get_context_size() -> int:
    return sum(len(e["command"]) + len(e["output"]) for e in command_history)


def add_to_history(command: str, output: str = ""):
    command_history.append(
        {"command": command, "output": output[:500] if output else ""}
    )
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
        if entry["output"]:
            output_lines = entry["output"].strip().split("\n")[:2]
            for line in output_lines:
                lines.append(f"   {line}")
    return "\n".join(lines)


def get_command(user_input: str, cwd: str) -> str:
    global client, current_provider, current_model

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

User request: {user_input}"""

    cfg = PROVIDERS[current_provider]
    model = current_model or cfg["default_model"]

    if current_provider == "gemini":
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text.strip()
    else:
        # OpenAI-compatible API (z.ai, zhipu)
        # GLM reasoning models need more tokens for thinking + response
        # Simple queries: ~200 tokens, Complex queries: ~500+ tokens
        response = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}], max_tokens=2000
        )
        return response.choices[0].message.content.strip()


def is_natural_language(text: str) -> bool:
    if text.startswith("!"):
        return False
    shell_commands = [
        "ls",
        "pwd",
        "clear",
        "exit",
        "quit",
        "whoami",
        "date",
        "cal",
        "top",
        "htop",
        "history",
        "which",
        "man",
        "touch",
        "head",
        "tail",
        "grep",
        "find",
        "sort",
        "wc",
        "diff",
        "tar",
        "zip",
        "unzip",
    ]
    shell_starters = [
        "cd ",
        "ls ",
        "echo ",
        "cat ",
        "mkdir ",
        "rm ",
        "cp ",
        "mv ",
        "git ",
        "npm ",
        "node ",
        "npx ",
        "python",
        "pip ",
        "brew ",
        "curl ",
        "wget ",
        "chmod ",
        "chown ",
        "sudo ",
        "vi ",
        "vim ",
        "nano ",
        "code ",
        "open ",
        "export ",
        "source ",
        "docker ",
        "kubectl ",
        "aws ",
        "gcloud ",
        "./",
        "/",
        "~",
        "$",
        ">",
        ">>",
        "|",
        "&&",
    ]
    if text in shell_commands:
        return False
    return not any(text.startswith(s) for s in shell_starters)


def main():
    global current_provider, current_model, client, gemini_client

    while True:
        try:
            cwd = os.getcwd()
            # Show provider indicator if not using default gemini
            if current_provider != "gemini":
                provider_tag = f"\033[35m[{current_provider}]\033[0m "
            else:
                provider_tag = ""
            prompt = f"{provider_tag}\033[32m{os.path.basename(cwd)}\033[0m > "
            user_input = input(prompt).strip()

            if not user_input:
                continue

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
                setup_api_key(current_provider, exit_on_empty=False)
                # Reinitialize client with new key
                if current_provider == "gemini":
                    global gemini_client
                    gemini_client = None
                    client = get_gemini_client()
                else:
                    client = get_openai_client(current_provider)
                continue

            if user_input == "!providers":
                print("\n\033[36mAvailable providers:\033[0m")
                for pid, cfg in PROVIDERS.items():
                    has_key = "✓" if os.getenv(cfg["env_key"]) else "✗"
                    marker = (
                        " \033[32m(active)\033[0m" if pid == current_provider else ""
                    )
                    print(f"  [{has_key}] {pid} - {cfg['name']}{marker}")
                print()
                continue

            if user_input.startswith("!provider"):
                parts = user_input.split()
                if len(parts) == 1:
                    cfg = PROVIDERS[current_provider]
                    model = current_model or cfg["default_model"]
                    print(f"\033[36mCurrent: {current_provider}/{model}\033[0m")
                    continue
                new_provider = parts[1].lower()
                if new_provider not in PROVIDERS:
                    print(f"\033[31mUnknown provider: {new_provider}\033[0m")
                    print(f"Available: {', '.join(PROVIDERS.keys())}")
                    continue
                # Check if API key exists, prompt if not
                cfg = PROVIDERS[new_provider]
                if not os.getenv(cfg["env_key"]):
                    print(f"\033[33mNo API key found for {cfg['name']}\033[0m")
                    if not setup_api_key(new_provider, exit_on_empty=False):
                        continue
                current_provider = new_provider
                current_model = None  # Reset to provider default
                if current_provider == "gemini":
                    client = get_gemini_client()
                else:
                    client = get_openai_client(current_provider)
                print(
                    f"\033[32m✓ Switched to {cfg['name']} ({cfg['default_model']})\033[0m"
                )
                continue

            if user_input == "!models":
                cfg = PROVIDERS[current_provider]
                print(f"\n\033[36mModels for {cfg['name']}:\033[0m")
                active_model = current_model or cfg["default_model"]
                for m in cfg["models"]:
                    marker = " \033[32m(active)\033[0m" if m == active_model else ""
                    default = " (default)" if m == cfg["default_model"] else ""
                    print(f"  - {m}{default}{marker}")
                print()
                continue

            if user_input.startswith("!model"):
                parts = user_input.split()
                if len(parts) == 1:
                    cfg = PROVIDERS[current_provider]
                    model = current_model or cfg["default_model"]
                    print(f"\033[36mCurrent model: {model}\033[0m")
                    continue
                new_model = parts[1]
                cfg = PROVIDERS[current_provider]
                if new_model not in cfg["models"]:
                    print(
                        f"\033[33mWarning: {new_model} not in known models, using anyway\033[0m"
                    )
                current_model = new_model
                print(f"\033[32m✓ Model set to {new_model}\033[0m")
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
                    sys.exit(0)
                continue

            if user_input == "!help":
                show_help()
                continue

            if user_input.startswith("!"):
                cmd = user_input[1:]
                if not cmd:
                    continue
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                print(result.stdout, end="")
                if result.stderr:
                    print(result.stderr, end="")
                add_to_history(cmd, result.stdout + result.stderr)
                continue

            if not is_natural_language(user_input):
                result = subprocess.run(
                    user_input, shell=True, capture_output=True, text=True
                )
                print(result.stdout, end="")
                if result.stderr:
                    print(result.stderr, end="")
                add_to_history(user_input, result.stdout + result.stderr)
                continue

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
                    result = subprocess.run(
                        command, shell=True, capture_output=True, text=True
                    )
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
