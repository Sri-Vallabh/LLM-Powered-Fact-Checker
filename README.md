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

# 🚀 LLM-Powered Fact Checker

A robust, end-to-end, AI-driven fact-checking pipeline for news and social media claims.  
It combines **web scraping**, **semantic search** with ChromaDB, and **large language models** (LLMs) via Groq/OpenAI API to deliver verdicts with transparent reasoning.  
Includes a modern Streamlit UI, user feedback logging, **secure encrypted storage**, and is fully CI/CD integrated with Hugging Face Spaces.

**Live Demo:**  
[https://huggingface.co/spaces/tsrivallabh/LLM-Powered-Fact-Checker](https://huggingface.co/spaces/tsrivallabh/LLM-Powered-Fact-Checker)

---

## ✨ Features

- **Automated PIB News Scraping:**  
  Uses `requests` and `BeautifulSoup` to scrape official PIB news feeds, extracting both titles and sources. Handles duplicates and ensures a clean, up-to-date evidence base.
- **Semantic Vector Search:**  
  Employs `sentence-transformers` and ChromaDB for fast, meaningful retrieval of the most relevant evidence for any claim.
- **LLM Fact Checking:**  
  Uses Llama-3-8B (via Groq API) or any OpenAI-compatible LLM to analyze claims against retrieved evidence, returning structured verdicts and reasoning.
- **Streamlit UI:**  
  Clean, interactive interface for claim entry, evidence review, and verdict explanation.
- **User Feedback Logging:**  
  Every verdict can be rated (👍/👎), and all feedback is logged with claim, verdict, evidence, and reasoning in a CSV for future analysis.
- **ChromaDB Encryption:**  
  All vector database files can be encrypted at rest using `cryptography` and Fernet, ensuring your data is secure even if the storage is compromised.
- **CI/CD Integrated:**  
  Every push to the [GitHub repo](https://github.com/Sri-Vallabh/LLM-Powered-Fact-Checker) automatically updates the Hugging Face Space via GitHub Actions.
- **Robust Error Handling:**  
  Handles LLM/JSON quirks, UI edge cases, and provides clear debugging output for any issues.

---

## 🌐 Live Demo

Try it now:  
[https://huggingface.co/spaces/tsrivallabh/LLM-Powered-Fact-Checker](https://huggingface.co/spaces/tsrivallabh/LLM-Powered-Fact-Checker)

---

## 🚦 Quickstart

### 1. **Clone the Repository**

```bash
git clone https://github.com/Sri-Vallabh/LLM-Powered-Fact-Checker.git
cd LLM-Powered-Fact-Checker
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
- This will fetch the latest PIB news, **handle duplicates**, and store both titles and sources in ChromaDB.

### 5. **(Optional) Encrypt ChromaDB**

For maximum security:

```bash
python encrypt_chroma.py
```
- Uses `cryptography` to encrypt your vector database at rest.

### 6. **Run the Streamlit App**

```bash
streamlit run app.py
```

---

## 🗂 File Structure

```
├── app.py                  # Streamlit UI
├── scrape_chroma.py        # PIB news scraping & ChromaDB population
├── encrypt_chroma.py       # Encrypt ChromaDB files (optional)
├── decrypt_chroma.py       # Decrypt ChromaDB files (optional)
├── fact_checker.py         # Core fact-checking logic
├── feedback_log.csv        # Stores user feedback
├── requirements.txt
├── .env
└── chroma_db/              # ChromaDB vector database (encrypted if enabled)
```

---

## 🛡 Security

- **API keys**: Managed via `.env` and Hugging Face Spaces Secrets—never hardcoded or committed.
- **ChromaDB Encryption:**  
  All evidence is stored encrypted at rest using `cryptography` and Fernet.  
  Only decrypted in memory at runtime.
- **CI/CD:**  
  Hugging Face Space is updated automatically via GitHub Actions on every push—no manual deployment needed.

---

## 🧠 How It Works

1. **Web Scraping:**  
   `scrape_chroma.py` fetches PIB RSS feeds, parses with BeautifulSoup, and stores unique news items and their sources in ChromaDB.
2. **Semantic Search:**  
   When a claim is entered, the app retrieves the most relevant evidence using vector similarity.
3. **LLM Fact Checking:**  
   The claim and evidence are sent to an LLM, which returns a verdict (`True`, `False`, or `Unverifiable`) and a step-by-step reasoning.
4. **Feedback Loop:**  
   Users can rate the verdict, and all feedback is logged for future improvements.

---

## 📝 Feedback & Contributions

- Feedback is stored in `feedback_log.csv` for transparency and future model improvement.
- Contributions, bug reports, and feature requests are welcome!  
  Please open an issue or pull request on [GitHub](https://github.com/Sri-Vallabh/LLM-Powered-Fact-Checker).

---

## 📦 Requirements

- Python 3.8+
- See `requirements.txt` for all Python dependencies.

### Main Dependencies

- `requests`, `beautifulsoup4`, `lxml` — Web scraping
- `chromadb`, `sentence-transformers` — Vector search
- `cryptography` — Encryption (optional)
- `openai` — LLM API client (Groq/OpenAI compatible)
- `streamlit` — User interface
- `python-dotenv` — Environment variable management

---

## 📣 Acknowledgements

- Built with ❤️ by Sri Vallabh Tammireddy
- Powered by [Groq](https://groq.com/), [Hugging Face](https://huggingface.co/), and the open-source community.

---

**Live Space:**  
[https://huggingface.co/spaces/tsrivallabh/LLM-Powered-Fact-Checker](https://huggingface.co/spaces/tsrivallabh/LLM-Powered-Fact-Checker)

---
