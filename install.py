import os
import platform
from pathlib import Path
import subprocess
import sys
import time

print("Please run as administrator if you are on Windows", flush=True)
print("Or grant execution permissions with chmod if you're on Linux", flush=True)

time.sleep(5)

try:
    from rich.prompt import Confirm
except ImportError:
    print("Installing the 'rich' UI library...", flush=True)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.prompt import Confirm


def main():
    try:
        info = platform.freedesktop_os_release()
        name_os = info.get("ID", "Unknown")
    except AttributeError:
        name_os = platform.system().lower()

    true_name_os = name_os.lower()

    if true_name_os == "unknown":
        print(f"Operating system {name_os} not supported", flush=True)
        sys.exit(1)

    if Confirm.ask(f"Is the operating system you are using {name_os}?", default=True):
        print("Creating virtual environment (.venv)...", flush=True)
        subprocess.check_call([sys.executable, "-m", "venv", ".venv"])

        if platform.system() == "Windows":
            pip_executable = Path(".venv") / "Scripts" / "pip"
        else:
            pip_executable = Path(".venv") / "bin" / "pip"

        try:
            print("Installing packages from requirements.txt into venv...", flush=True)
            subprocess.check_call(
                [str(pip_executable), "install", "-r", "requirements.txt"]
            )
        except Exception as e:
            print(f"Error while installing requirements: {e}", flush=True)

        if Path(".env").is_file():
            print(".env file is ready", flush=True)
        else:
            env_content = """PORT=5000
                    DEBUG=True
                    TEST=True
                    
                    GITHUB_TOKEN=your_github_token_classic
                    NAME_GITHUB=your_github_name
                    MONGO_URI=your_mongodb_url
                    
                    DB_NAME=your_db_name
                    DB_COLLECTION=your_db_collection_in_db_name
            """
            with open(".env", "w", encoding="utf-8") as f:
                f.write(env_content.strip() + "\n")
            print(".env file is ready", flush=True)
    else:
        print("Installation cancelled by user.")


if __name__ == "__main__":
    main()
    print("Environment setup complete.", flush=True)
