# Zero AI Terminal 🚀

![Status](https://img.shields.io/badge/status-in_development-orange)
![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)

An experimental, AI-powered command-line assistant that translates your plain English instructions into executable shell commands. Powered by a custom-trained `CodeGemma` model.


---

## 🚧 Project Status

This project is currently in the early stages of development. The core functionality is working, but it's still an MVP (Minimum Viable Product). Expect bugs and exciting new features to come!

---

## ✨ Features

* **Translate natural language** into precise bash commands.
* **Auto-downloads** the required model from Hugging Face on the first run.
* Includes a critical **safety check** (confirmation prompt) before executing any command.

---

## 🛠️ Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/sanjayy0612/zero_..git](https://github.com/sanjayy0612/zero_..git)
    cd zero_..
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv ai_ter
    source ai_ter/bin/activate
    ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

---

## ▶️ How to Use

Simply run the main script from your terminal:

```bash
python zero.py
