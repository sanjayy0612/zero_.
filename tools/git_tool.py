import subprocess
import sys
from utils.constants import colors
from groq import Groq


try:
    with open("prompts/git_commit_prompt.txt", "r") as f:
        GIT_COMMIT_PROMPT = f.read()
except FileNotFoundError:
    print(f"{colors.RED}Error: 'prompts/git_commit_prompt.txt' not found.{colors.END}")
    sys.exit(1)

def run_git_commit(groq_client: Groq):
    """Generates an AI commit message based on staged git changes."""
    print(f"{colors.BLUE}Running AI Git Commit...{colors.END}")
    
    try:
        # 1. Get the staged changes
        diff_result = subprocess.run(
            ["git", "diff", "--staged"], 
            capture_output=True, text=True, check=True
        )
        
        if not diff_result.stdout:
            print(f"{colors.YELLOW}No staged changes found. Please `git add` files to commit.{colors.END}")
            return

        diff_content = diff_result.stdout
        
        # 2. Create a high-quality prompt for the chat model
        messages = [
            {"role": "system", "content": GIT_COMMIT_PROMPT},
            {"role": "user", "content": f"Based on this diff, write the commit message:\n\n{diff_content}"}
        ]

        print(f"{colors.BLUE}Analyzing diff... (This may take a moment){colors.END}")
        
        # 3. Generate the commit message using the passed Groq client
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.2,
            max_tokens=150
        )
        
        commit_message = completion.choices[0].message.content.strip()
        
        # 4. Confirm with the user
        print(f"\n{colors.YELLOW}Suggested commit message:{colors.END}")
        print(f"{colors.GREEN}{commit_message}{colors.END}")
        confirmation = input(f"\n{colors.YELLOW}Commit with this message? [y/N]: {colors.END}").lower()
        
        # 5. Execute the commit
        if confirmation == 'y':
            print(f"{colors.BLUE}Executing commit...{colors.END}")
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True, text=True
            )
            if commit_result.stderr:
                print(f"{colors.RED}{commit_result.stderr}{colors.END}")
            else:
                print(f"{colors.GREEN}Successfully committed!{colors.END}")
                print(commit_result.stdout)
        else:
            print(f"   {colors.BLUE}Commit cancelled.{colors.END}")

    except subprocess.CalledProcessError as e:
        print(f"{colors.RED}Error: Not a git repository or no staged files.\n{e.stderr}{colors.END}")
    except Exception as e:
        print(f"{colors.RED}An error occurred: {e}{colors.END}")