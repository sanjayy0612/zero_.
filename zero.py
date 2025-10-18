import subprocess
import os
from llama_cpp import Llama
from huggingface_hub import hf_hub_download

# --- Configuration ---
REPO_ID = "Sanjayyy06/zero-nl2cmds-v1"
MODEL_NAME = "zero-nl2cmds-v1.Q4_K_M.gguf"

# ANSI color codes
class colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

# --- Get the Model ---
# This new section handles finding or downloading the model file.
model_path = ""
# First, check if the model exists in the same directory as the script
local_model_path = os.path.join(os.path.dirname(__file__), MODEL_NAME)

if os.path.exists(local_model_path):
    print(f"{colors.BLUE}Found model locally at: {local_model_path}{colors.END}")
    model_path = local_model_path
else:
    try:
        print(f"{colors.BLUE}Model not found locally. Downloading from '{REPO_ID}'...{colors.END}")
        # Download the model from Hugging Face Hub. It will be cached automatically.
        model_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=MODEL_NAME
        )
        print(f"{colors.GREEN}Download complete! Model is at: {model_path}{colors.END}")
    except Exception as e:
        print(f"{colors.RED}Failed to download model: {e}{colors.END}")
        exit()

# --- Load the Model ---
print(f"{colors.BLUE}Loading model...{colors.END}")
try:
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_gpu_layers=-1, # Offload all layers to GPU on Apple Silicon
        verbose=False
    )
except Exception as e:
    print(f"{colors.RED}Error loading model: {e}{colors.END}")
    exit()

print(f"{colors.GREEN}Model loaded! Welcome to Zero AI Terminal.{colors.END}")

# --- Main Application Loop ---
# (This part remains exactly the same)
while True:
    try:
        natural_language_query = input(f"\n{colors.YELLOW}>> {colors.END}")
        if natural_language_query.lower() in ["exit", "quit"]:
            break

        prompt = f"Instruction: {natural_language_query}\nOutput:"
        output = llm(
            prompt, max_tokens=100, stop=["\n"], temperature=0.1, echo=False
        )
        command = output["choices"][0]["text"].strip()

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