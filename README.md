---
title: LLM Powered Fact Checker
emoji: 🚀
colorFrom: red
colorTo: red
sdk: docker
app_port: 8501
tags:
  - streamlit
pinned: false
short_description: Streamlit template space
license: mit
---

# LLM-Powered Fact Checker

A robust, end-to-end fact-checking pipeline for news and social media claims, using ChromaDB for semantic evidence retrieval and LLMs (via Groq/OpenAI API) for verdicts. Includes a Streamlit UI, feedback CSV logging, and optional local encryption for data privacy.

---

## Features

- **Automated PIB News Scraping:** Fetches and stores latest PIB headlines and sources.
- **Semantic Vector Search:** Uses ChromaDB and sentence-transformers for evidence retrieval.
- **LLM Fact Checking:** Verdicts and reasoning from Llama-3-8B (via Groq API).
- **Streamlit UI:** User-friendly claim verification interface.
- **User Feedback Logging:** Stores user feedback with claim, verdict, evidence, and reasoning in a CSV.
- **Data Encryption (Optional):** Encrypts/decrypts your ChromaDB database at rest.
- **Robust Error Handling:** Handles LLM/JSON quirks and UI edge cases.

---

## Quickstart

### 1. **Clone the Repository**

```bash
git clone https://github.com/Sri-Vallabh/LLM-Powered-Fact-Checker.git
cd LLM-Powered-Face-Checker
```

### 2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 3. **Set Up Environment Variables**

Create a `.env` file in the root directory:

```
GROQ_API_KEY=your-groq-api-key-here
```

### 4. **Scrape PIB News and Populate ChromaDB**

```bash
python scrape_chroma.py
```

### 5. **(Optional) Encrypt ChromaDB**

```bash
python encrypt_chroma.py
```

### 6. **Run the Streamlit App**

```bash
streamlit run app.py
```

---

## File Structure

```
├── app.py                  # Streamlit UI
├── scrape_chroma.py        # PIB news scraping & ChromaDB population
├── encrypt_chroma.py       # Encrypt ChromaDB files (optional)
├── decrypt_chroma.py       # Decrypt ChromaDB files (optional)
├── fact_checker.py         # Core fact-checking logic
├── feedback_log.csv        # Stores user feedback
├── requirements.txt
├── .env
└── chroma_db/              # ChromaDB vector database
```

---

## Usage

1. **Enter a claim** in the Streamlit UI.
2. **Review the verdict, supporting evidence, and reasoning.**
3. **Provide feedback** (👍/👎) — your feedback is logged for continuous improvement.

---

## Requirements

- Python 3.8+
- See `requirements.txt` for all Python dependencies.

---

## Main Dependencies

- `requests`, `beautifulsoup4`, `lxml` — Web scraping
- `chromadb`, `sentence-transformers` — Vector search
- `cryptography` — Encryption (optional)
- `openai` — LLM API client (Groq/OpenAI compatible)
- `streamlit` — User interface
- `python-dotenv` — Environment variable management

---

## Security

- **API keys**: Never share your `.env` file.
- **Encryption**: Use `encrypt_chroma.py` and `decrypt_chroma.py` to keep your database secure at rest.

---

## Feedback & Contributions

- Feedback is logged in `feedback_log.csv`.
- Contributions, bug reports, and feature requests are welcome! Please open an issue or pull request.

---

## License

MIT License

---

**Built with ❤️ by [Your Name/Team]**

---

Feel free to customize the repo URL, author, or any section as needed!