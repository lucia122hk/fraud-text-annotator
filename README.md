# Fraud Text Annotator

A multi‑label fraud annotation toolkit for social media and news texts. It provides both a **local web application** (batch annotation via folder or single text input) and **Jupyter notebooks** for large‑scale batch processing. The toolkit classifies fraud texts using a **16‑dimensional taxonomy** (Gain, Loss, Role, Control) and extracts **temporal sequence labels** to reconstruct fraud scripts.

## Features

- **16 tactical labels** (G1..G3, L1..L3, R1..R3, C1..C5, OT, NS) + **temporal sequence** (e.g., `["R2","L2","G1"]`)
- Two workflows:
  - **Web app** – upload a file or enter text, get instant annotation
  - **Batch notebooks** – run on entire datasets via LLM API (OpenAI‑compatible)
- Data cleaning and inter‑rater agreement analysis included
- Designed for social media posts (LIHKG, Reddit, Facebook, etc.) and fraud news articles

## Repository Structure

    fraud-text-annotator/
    ├── README.md
    ├── LICENSE
    ├── .gitignore
    ├── notebooks/
    │   ├── 16Label.ipynb
    │   ├── TimeLabel.ipynb
    │   ├── datacleaning.ipynb
    │   └── human_human_llm_consistency.ipynb
    └── web_app/
        ├── backend/
        ├── frontend
        ├── start_backend.sh
        ├── start_frontend.sh
        ├── README.md
        └── requirements.txt/
        

## Getting Started

### 1. Clone the repository

    git clone https://github.com/yourusername/fraud-text-annotator.git
    cd fraud-text-annotator

### 2. Set up a virtual environment (recommended)

    python -m venv venv
    source venv/bin/activate        # On Windows: venv\Scripts\activate

### 3. Install dependencies

    pip install -r requirements.txt

Typical dependencies: `openai`, `pandas`, `flask`, `flask-cors`, `jupyter`, `requests`.

### 4. Configure your LLM API (Qwen or any OpenAI‑compatible API)

The code examples use **Qwen** (DashScope) by default, but you can replace it with any OpenAI‑compatible endpoint (e.g., GPT‑4, DeepSeek, local vLLM).  

For the **notebooks**, edit the `api_key`, `base_url`, and `model_name` variables inside the notebook. For the **web app**, set environment variables (see below).

**Example using Qwen (DashScope):**

    export DASHSCOPE_API_KEY="your-qwen-key"

**Example using OpenAI‑compatible endpoint (e.g., GPT‑4):**

    export OPENAI_API_KEY="your-key"
    export OPENAI_BASE_URL="https://api.openai.com/v1"   # optional

The notebooks and backend code are designed to work with any API that follows the `/chat/completions` interface.

### 5. Run the web application

    cd web_app
    python backend/app.py          # or ../start_backend.sh

Then in another terminal, open `frontend/index.html` or run `start_frontend.sh`.

### 6. Use the batch annotation notebooks

Launch Jupyter:

    jupyter notebook

Open the notebooks in the `notebooks/` folder:

- `datacleaning.ipynb` – clean raw data (remove empty/duplicate texts)
- `16Label.ipynb` – annotate 16 tactical labels (G1..C5, OT, NS)
- `TimeLabel.ipynb` – annotate temporal sequence (e.g., `["R2","L2","G1"]`)
- `human_human_llm_consistency.ipynb` – compute inter‑rater agreement

Adjust the input file paths and API parameters inside each notebook.

## Data Cleaning & Inter‑Rater Agreement

- `datacleaning.ipynb` – remove empty texts, duplicates, and basic preprocessing.
- `human_human_llm_consistency.ipynb` – compute Cohen’s Kappa / Krippendorff’s alpha between human annotators and LLM‑generated labels.

## Customising the Taxonomy

The framework follows a **narrative‑present vs. narrative‑absent** principle. See the code and comments inside the notebooks for the full label definitions (G1..C5).

## Requirements

- Python 3.8+
- LLM API access (Qwen, OpenAI, or any OpenAI‑compatible endpoint) – costs may apply
- 4+ GB RAM for batch processing large datasets

## License

MIT
