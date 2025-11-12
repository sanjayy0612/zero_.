# The main entry point and router for the Zero AI Terminal.

import argparse
import sys
from dotenv import load_dotenv
from groq import Groq
from utils.constants import colors

# --- 1. Load .env file at the VERY start ---
# This makes environment variables (like GROQ_API_KEY) available
load_dotenv()

def main():
    parser = argparse.ArgumentParser(
        description="Zero AI Terminal Assistant",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--analyze",
        metavar="URL",
        type=str,
        help="Analyze a GitHub repository URL."
    )
    group.add_argument(
        "--git",
        metavar="TASK",
        type=str,
        help="Run an AI-powered git task (e.g., 'commit')."
    )

    args = parser.parse_args()
    
    # --- 2. The Main Router Logic ---
    # We now load models and clients *inside* the logic block,
    # so we only load what we need for the specific task.

    if args.analyze:
        # --- Analyze Tool ---
        # This tool only needs the Groq client.
        try:
            # We initialize the client *after* load_dotenv() has run
            groq_client = Groq() 
            from tools.analyze_tool import run_github_analyzer
            # We pass the client to the tool
            run_github_analyzer(groq_client, args.analyze)
        except Exception as e:
            print(f"{colors.RED}Failed to start analyze tool: {e}{colors.END}")
            print(f"{colors.YELLOW}Make sure 'GROQ_API_KEY' is in your .env file.{colors.END}")
    
    elif args.git:
        # --- Git Tool ---
        # This tool also uses the Groq client.
        if args.git.lower() == 'commit':
            try:
                groq_client = Groq()
                from tools.git_tool import run_git_commit
                # We pass the client to the tool
                run_git_commit(groq_client)
            except Exception as e:
                print(f"{colors.RED}Failed to start git tool: {e}{colors.END}")
                print(f"{colors.YELLOW}Make sure 'GROQ_API_KEY' is in your .env file.{colors.END}")
        else:
            print(f"{colors.RED}Unknown git task: '{args.git}'. Did you mean 'commit'?{colors.END}")
    
    else:
        # --- Default Shell Tool ---
        # This is the only tool that needs the local Llama model.
        try:
            from utils.model_loader import load_model
            from tools.shell_tool import start_interactive_loop
            llm = load_model()
            start_interactive_loop(llm)
        except Exception as e:
            print(f"{colors.RED}Failed to start interactive shell: {e}{colors.END}")

if __name__ == "__main__":
    main()