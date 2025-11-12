import subprocess
import sys
import re
from utils.constants import colors
from groq import Groq

# Load the system prompt from the file
try:
    with open("prompts/git_commit_prompt.txt", "r") as f:
        GIT_COMMIT_PROMPT = f.read()
except FileNotFoundError:
    print(f"{colors.RED}Error: 'prompts/git_commit_prompt.txt' not found.{colors.END}")
    sys.exit(1)

# --- Helper Functions for Advanced Logic ---

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
    # Simple regex for keys like gsk_..., sk_..., etc.
    patterns = [
        r"(gsk|sk|pk)_[a-zA-Z0-9]{40,}", # Groq, Stripe, etc.
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
    
    return "Refactor" # A safe default

# --- Main Tool Function ---

def run_git_commit(groq_client: Groq):
    """Generates an AI commit message based on staged git changes."""
    print(f"{colors.BLUE}Gathering context from your repository...{colors.END}")
    
    # 1. Collect all Git context
    context = _collect_git_context()
    if "error" in context:
        print(f"{colors.RED}Error: {context['error']}{colors.END}")
        return

    # 2. Run Safety Check
    is_safe, message = _check_for_secrets(context["diff"])
    if not is_safe:
        print(f"{colors.RED}CRITICAL: Safety check failed! {message}{colors.END}")
        print(f"{colors.YELLOW}Commit aborted to prevent leaking secrets.{colors.END}")
        return
    
    # 3. Auto-detect commit type
    commit_type_hint = _auto_detect_type(context["files"], context["branch"])
    
    print(f"{colors.BLUE}Analyzing diff... (Branch: {context['branch']}, Type: {commit_type_hint}){colors.END}")

    # 4. Build the final prompt
    # Truncate diff if it's too long for the prompt
    MAX_DIFF_LEN = 4000 
    diff_for_prompt = context['diff']
    if len(diff_for_prompt) > MAX_DIFF_LEN:
        diff_for_prompt = diff_for_prompt[:MAX_DIFF_LEN] + "\n... (Diff truncated)"

    prompt = GIT_COMMIT_PROMPT.replace("{{BRANCH}}", context["branch"])
    prompt = prompt.replace("{{TYPE_HINT}}", commit_type_hint)
    prompt = prompt.replace("{{RECENT_LOG}}", context["log"])
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": diff_for_prompt}
    ]

    # 5. Generate the commit message using Groq
    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b", # Your powerful 20B model
            messages=messages,
            temperature=0.2, # Low temperature for factual, non-creative commits
            max_tokens=250   # Allow for a subject + body
        )
        
        commit_message = completion.choices[0].message.content.strip()
        
        # 6. Confirm with the user
        print(f"\n{colors.YELLOW}Suggested commit message:{colors.END}")
        print(f"{colors.GREEN}{commit_message}{colors.END}")
        confirmation = input(f"\n{colors.YELLOW}Commit with this message? [y/N]: {colors.END}").lower()
        
        # 7. Execute the commit
        if confirmation == 'y':
            print(f"{colors.BLUE}Executing commit...{colors.END}")
            # We must pass the multi-line message as a single argument
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