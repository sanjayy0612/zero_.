import subprocess
import sys
from utils.constants import colors


try:
    with open("prompts/shell_prompt.txt", "r") as f:
        SHELL_SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    print(f"{colors.RED}Error: 'prompts/shell_prompt.txt' not found.{colors.END}")
    sys.exit(1)

def start_interactive_loop(llm):
    """Starts the main interactive shell loop."""
    print(f"{colors.GREEN}Welcome to Zero AI Terminal. Type 'exit' or 'quit' to end.{colors.END}")
    
    while True:
        try:
            natural_language_query = input(f"\n{colors.YELLOW}>> {colors.END}")
            if natural_language_query.lower() in ["exit", "quit"]:
                break

            
            messages = [
                {"role": "system", "content": SHELL_SYSTEM_PROMPT},
                {"role": "user", "content": natural_language_query}
            ]
            
            output = llm.create_chat_completion(
                messages=messages,
                temperature=0.1,
                max_tokens=100
            )
            command = output['choices'][0]['message']['content'].strip(" \n`")

            if not command:
                print(f"{colors.RED}Sorry, I couldn't generate a command.{colors.END}")
                continue

            print(f"   {colors.BLUE}Suggested command: {colors.END}{colors.GREEN}{command}{colors.END}")
            confirmation = input(f"   {colors.YELLOW}Execute? [y/N]: {colors.END}").lower()

            if confirmation == 'y':
                print(f"   {colors.BLUE}Executing...{colors.END}")
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(f"{colors.RED}{result.stderr}{colors.END}")
            else:
                print(f"   {colors.BLUE}Execution cancelled.{colors.END}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"{colors.RED}An error occurred: {e}{colors.END}")