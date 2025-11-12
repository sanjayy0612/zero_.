import subprocess
import sys
import re
from utils.constants import colors
from groq import Groq

# Load the system prompt from the file
try:
    with open("prompts/git_commit_prompt.txt", "r") as f:
        GIT_SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    print(f"{colors.RED}Error: 'prompts/git_commit_prompt.txt' not found.{colors.END}")
    sys.exit(1)

# --- Helper Functions (No Changes) ---

def _collect_git_context():
    """Gathers all necessary context from the local git repository."""
    try:
        diff_content = subprocess.check_output(
            ["git", "diff", "--staged"], text=True
        ).strip()
        
        if not diff_content:
            return {"error": "No staged changes found. Please `git add` files to commit."}

        branch_name = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
        ).strip()
        
        recent_log = subprocess.check_output(
            ["git", "log", "-3", "--oneline"], text=True
        ).strip()
        
        files_changed = subprocess.check_output(
            ["git", "diff", "--staged", "--name-only"], text=True
        ).strip().split('\n')

        return {
            "diff": diff_content,
            "branch": branch_name,
            "log": recent_log,
            "files": files_changed
        }
    except subprocess.CalledProcessError as e:
        return {"error": f"Not a git repository or git error: {e}"}

def _check_for_secrets(diff_content):
    """Scans the diff for common secret patterns."""
    patterns = [
        r"(gsk|sk|pk)_[a-zA-Z0-9]{40,}", 
        r"API_KEY\s*=\s*['\"][a-zA-Z0-9_]{16,}['\"]",
        r"SECRET_KEY\s*=\s*['\"][a-zA-Z0-9_]{16,}['\"]"
    ]
    for pattern in patterns:
        if re.search(pattern, diff_content):
            return False, f"Potential secret found: {pattern}"
    return True, "No secrets found."

def _auto_detect_type(files, branch):
    """Provides a 'hint' to the AI about the commit type."""
    branch_lower = branch.lower()
    if "fix/" in branch_lower or "bug/" in branch_lower:
        return "Fix"
    if "feat/" in branch_lower or "feature/" in branch_lower:
        return "Feat"
    if any(f.endswith('.md') for f in files) or "docs/" in branch_lower:
        return "Docs"
    if any(f.startswith('tests/') or f.endswith('_test.py') for f in files):
        return "Test"
    if any(f in ['requirements.txt', 'package.json', '.github/'] for f in files):
        return "Chore"
    return "Refactor" 

# --- Main Tool Function ---

def run_git_commit(groq_client: Groq):
    """Generates an AI commit message based on staged git changes."""
    print(f"{colors.BLUE}Gathering context from your repository...{colors.END}")
    
    context = _collect_git_context()
    if "error" in context:
        print(f"{colors.RED}Error: {context['error']}{colors.END}")
        return

    is_safe, message = _check_for_secrets(context["diff"])
    if not is_safe:
        print(f"{colors.RED}CRITICAL: Safety check failed! {message}{colors.END}")
        print(f"{colors.YELLOW}Commit aborted to prevent leaking secrets.{colors.END}")
        return
    
    commit_type_hint = _auto_detect_type(context["files"], context["branch"])
    print(f"{colors.BLUE}Analyzing diff... (Branch: {context['branch']}, Type: {commit_type_hint}){colors.END}")

    MAX_DIFF_LEN = 4000 
    diff_for_prompt = context['diff']
    if len(diff_for_prompt) > MAX_DIFF_LEN:
        diff_for_prompt = diff_for_prompt[:MAX_DIFF_LEN] + "\n... (Diff truncated)"

    user_prompt = f"""
    Please generate a commit message based on the following context.

    ### CONTEXT:
    -   **Current Branch:** {context["branch"]}
    -   **Commit Type Hint:** {commit_type_hint}
    -   **Recent Commits:** {context["log"]}

    ### CODE DIFF TO ANALYZE:
    ```diff
    {diff_for_prompt}
    ```
    """
    
    messages = [
        {"role": "system", "content": GIT_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    try:
        print(f"\n{colors.YELLOW}Suggested commit message:{colors.END}")
        print(f"{colors.GREEN}", end="", flush=True)
        
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b", # Using your preferred model
            messages=messages,
            temperature=0.2, 
            max_tokens=250,
            stream=True
        )
        
        commit_message = ""
        for chunk in completion:
            chunk_content = chunk.choices[0].delta.content or ""
            commit_message += chunk_content
            print(chunk_content, end="", flush=True)
        
        print(f"{colors.END}")

        # --- THIS IS YOUR NEW FALLBACK LOGIC ---
        if not commit_message.strip():
            print(f"\n{colors.YELLOW}AI failed to generate a detailed message (empty response).{colors.END}")
            print(f"{colors.YELLOW}Generating a simple fallback commit message...{colors.END}")
            
            # Create a simple message, e.g., "Refactor: Updated 2 file(s)"
            file_count = len(context["files"])
            s = 's' if file_count > 1 else ''
            
            # List the files in the commit body
            file_list = "\n- ".join(context["files"])
            commit_message = f"{commit_type_hint}: Update {file_count} file{s}\n\nUpdated the following files:\n- {file_list}"
            
            # Print the fallback message for the user
            print(f"\n{colors.YELLOW}Suggested commit message (fallback):{colors.END}")
            print(f"{colors.GREEN}{commit_message}{colors.END}")
        # --- END OF FALLBACK LOGIC ---

        confirmation = input(f"\n{colors.YELLOW}Commit with this message? [y/N]: {colors.END}").lower()
        
        if confirmation == 'y':
            print(f"{colors.BLUE}Executing commit...{colors.END}")
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True, text=True
            )
            if commit_result.stderr and "nothing to commit" not in commit_result.stderr:
                print(f"{colors.RED}{commit_result.stderr}{colors.END}")
            else:
                print(f"{colors.GREEN}Successfully committed!{colors.END}")
                print(commit_result.stdout)
        else:
            print(f"   {colors.BLUE}Commit cancelled.{colors.END}")

    except Exception as e:
        print(f"{colors.RED}An error occurred during Groq API call: {e}{colors.END}")