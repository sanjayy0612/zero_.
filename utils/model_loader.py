import os
import sys
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
from utils.constants import colors, REPO_ID, MODEL_NAME, MODEL_DIR, MODEL_PATH

def load_model():
    """
    Finds the model file locally. If it doesn't exist,
    downloads it from Hugging Face Hub, then loads it into memory.
    """
    
    # Ensure the 'models' directory exists
    os.makedirs(MODEL_DIR, exist_ok=True)

    if os.path.exists(MODEL_PATH):
        print(f"{colors.BLUE}Found model locally at: {MODEL_PATH}{colors.END}")
    else:
        # This is the "else" block you were missing, built from the docs
        try:
            print(f"{colors.BLUE}Model not found. Downloading from '{REPO_ID}'...{colors.END}")
            # This is the function we "looked up"
            hf_hub_download(
                repo_id=REPO_ID,
                filename=MODEL_NAME,
                local_dir=MODEL_DIR,
                local_dir_use_symlinks=False
            )
            print(f"{colors.GREEN}Download complete! Model is at: {MODEL_PATH}{colors.END}")
        except Exception as e:
            print(f"{colors.RED}Failed to download model: {e}{colors.END}")
            sys.exit(1) # Exit the script if the model can't be found

    print(f"{colors.BLUE}Loading model... (This may take a moment){colors.END}")
    try:
        # These are the corrected parameters we "looked up"
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=2048,          # Context size (2048 is a good default)
            n_gpu_layers=-1,     # **CRITICAL**: Offload all layers to your Mac's GPU
            chat_format="chatml",# **CRITICAL**: Fixes the "chatty" Phi-3 model problem
            verbose=False      # Clean up the console output
        )
        print(f"{colors.GREEN}Model loaded!{colors.END}")
        return llm
    except Exception as e:
        print(f"{colors.RED}Error loading model: {e}{colors.END}")
        sys.exit(1)