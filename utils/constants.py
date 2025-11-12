import os


MODEL_DIR = "models"


REPO_ID = "Sanjayyy06/zero-nl2cmds-v1"
MODEL_NAME = "zero-nl2cmds-v1.Q4_K_M.gguf"


MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)


# --- ANSI Color Codes ---
class colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[34m'
    END = '\033[0m'