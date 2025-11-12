import requests
import base64
import json
import sys
import os
from utils.constants import colors
from groq import Groq 

# --- 1. Load the System Prompt ---
try:
    with open("prompts/analyze_repo_prompt.txt", "r") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    print(f"{colors.RED}Error: 'prompts/analyze_repo_prompt.txt' not found.{colors.END}")
    sys.exit(1)

# --- 2. Configuration ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") # Securely get token from environment
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# --- Helper Functions ---

def parse_repo_url(repo_url):
    """Extracts 'owner/repo' from 'https://github.com/owner/repo'."""
    try:
        if "github.com/" not in repo_url:
            if len(repo_url.split('/')) == 2:
                return repo_url
            else:
                raise ValueError("Invalid format")
        
        parts = repo_url.split("github.com/")[1].split("/")
        owner = parts[0]
        repo = parts[1].replace(".git", "")
        return f"{owner}/{repo}"
    except Exception:
        return None

def fetch_api_data(endpoint):
    """Fetches data from a given GitHub API endpoint."""
    url = f"https://api.github.com/repos/{endpoint}"
    print(f"{colors.BLUE}Fetching: {url}{colors.END}")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status() # Raises an error for 4xx or 5xx
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"{colors.RED}Error: Repository not found at {url}.{colors.END}")
        elif e.response.status_code == 403:
            print(f"{colors.RED}Error: GitHub API rate limit exceeded. {colors.END}")
            print(f"{colors.YELLOW}Try setting a GITHUB_TOKEN to increase the limit.{colors.END}")
        else:
            print(f"{colors.RED}API Error: {e}{colors.END}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"{colors.RED}Network Error: {e}{colors.END}")
        return None

def get_repo_data(repo_path):
    """Fetches all repository data in one go."""
    print(f"{colors.BLUE}--- Starting Analysis for {repo_path} ---{colors.END}")
    
    repo_data = fetch_api_data(repo_path)
    if not repo_data: return None

    lang_data = fetch_api_data(f"{repo_path}/languages")
    if not lang_data: return None

    readme_data = fetch_api_data(f"{repo_path}/readme")
    if not readme_data or 'content' not in readme_data:
        readme_content = "No README file found."
    else:
        try:
            readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
        except Exception as e:
            readme_content = f"Error decoding README: {e}"
            
    return repo_data, lang_data, readme_content

# ---
# THIS FUNCTION IS NOW FIXED
# ---
def build_user_prompt(repo_data, lang_data, readme_content):
    """Builds the final prompt context for the LLM."""
    print(f"{colors.BLUE}Building context for AI...{colors.END}")
    
    MAX_README_LEN = 3000
    if len(readme_content) > MAX_README_LEN:
        readme_content = readme_content[:MAX_README_LEN] + "\n... (README truncated)"

    # --- Robust data extraction ---
    # We use 'or {}' to ensure we have a dictionary, not None
    # We use .get() to safely access keys that might not exist
    
    license_info = repo_data.get('license') or {} 
    
    user_prompt = f"""
    Repository Name: {repo_data.get('name') or 'N/A'}
    Description: {repo_data.get('description') or 'N/A'}
    Languages: {json.dumps(lang_data, indent=2)}
    Stars: {repo_data.get('stargazers_count') or 'N/A'}
    License: {license_info.get('name') or 'N/A'}

    --- README.md Content ---
    {readme_content}
    """
    return user_prompt

# --- Main Tool Function ---

def run_github_analyzer(groq_client: Groq, repo_url: str):
    """
    Analyzes a GitHub repository using the GitHub API and Groq.
    This function now receives the initialized Groq client.
    """
    
    # 1. Parse the URL
    repo_path = parse_repo_url(repo_url)
    if not repo_path:
        print(f"{colors.RED}Error: Invalid GitHub URL '{repo_url}'. Please use 'https://github.com/owner/repo'.{colors.END}")
        return

    # 2. Fetch all data from GitHub
    data = get_repo_data(repo_path)
    if not data:
        return # Error messages are handled inside get_repo_data
    
    # 3. Build the prompt for the LLM
    # This function is now safe from 'None' errors
    user_prompt = build_user_prompt(data[0], data[1], data[2])

    # 4. Define the chat messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    # 5. Get the summary from Groq
    print(f"{colors.BLUE}Generating summary via Groq... (This will be fast!){colors.END}")
    
    print("\n" + "="*30)
    print(f" {colors.GREEN}AI Analysis of {repo_path}{colors.END} ")
    print("="*30 + "\n")
    
    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b", # Using your preferred model
            messages=messages,
            temperature=0.2,
            max_tokens=1024,
            stream=True,
            stop=None
        )
        
        # This is the correct way to stream the output
        for chunk in completion:
            print(chunk.choices[0].delta.content or "", end="")
        
        print("\n") # Add a newline after the stream is done

    except Exception as e:
        print(f"{colors.RED}\nAn error occurred during Groq API call: {e}{colors.END}")