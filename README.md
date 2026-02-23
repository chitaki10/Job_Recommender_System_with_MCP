# 💼 AI Job Recommender System with MCP

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA3.3--70B-orange?logo=groq)
![Apify](https://img.shields.io/badge/Jobs%20API-Apify-00B4D8?logo=apify)
![MCP](https://img.shields.io/badge/MCP-Tool%20Server-blueviolet)
![License](https://img.shields.io/badge/License-MIT-green)

> Upload your résumé and get **AI-powered job recommendations**, skill
> gap analysis, and a personalized career roadmap --- powered by Groq
> LLaMA 3.3-70B and real-time job listings from LinkedIn & Naukri via
> Apify.

🔗 **Live Demo:**\
https://chitaki10-job-recommender-system-with-mcp-app-eynbly.streamlit.app

------------------------------------------------------------------------

## 📌 Table of Contents

-   Features
-   Architecture
-   Tech Stack
-   Getting Started
-   API Keys Setup
-   MCP Tool Server
-   Project Structure
-   Results
-   License

------------------------------------------------------------------------

## ✨ Features

-   📄 Resume Parsing --- Extracts raw text from uploaded PDF résumés
    using PyMuPDF\
-   🧠 Resume Summary --- LLM summarizes your skills, experience, and
    profile in seconds\
-   🔍 Skill Gap Analysis --- Identifies missing skills, certifications,
    and areas to improve\
-   🗺️ Career Roadmap --- Personalized 6--12 month plan: skills to
    learn, projects to build, certs to pursue\
-   💼 Real-Time Job Recommendations --- Fetches live jobs from LinkedIn
    and Naukri via Apify API\
-   🔧 MCP Tool Server --- Core functions exposed as MCP tools

------------------------------------------------------------------------

## 🏗️ Architecture

    User uploads Résumé (PDF)
    │
    ▼
    Extract PDF Text (PyMuPDF)
    │
    ▼
    Groq LLaMA 3.3-70B (LLM)
    │
    ├── Summary
    ├── Skill Gap
    ├── Career Roadmap
    └── Job Keywords
    │
    ├──────────────┬───────────────┐
    ▼              ▼
    LinkedIn Jobs  Naukri Jobs
    (Apify Actor)  (Apify Actor)
    │
    └──────────────┬───────────────┘
    ▼
    Job Recommendations UI

------------------------------------------------------------------------

## 🛠️ Tech Stack

  Component         Technology
  ----------------- --------------------------------------
  UI                Streamlit
  LLM               Groq API --- llama-3.3-70b-versatile
  PDF Parsing       PyMuPDF (fitz)
  Job Scraping      Apify
  MCP Server        mcp Python SDK
  Package Manager   uv
  Deployment        Streamlit Cloud

------------------------------------------------------------------------

## 🚀 Getting Started

### Clone Repository

``` bash
git clone https://github.com/chitaki10/Job_Recommender_System_with_MCP.git
cd Job_Recommender_System_with_MCP
```

### Install Dependencies

``` bash
uv venv
uv add -r requirements.txt
```

### Create .env file

    GROQ_API_KEY=your_groq_api_key_here
    APIFY_API_TOKEN=your_apify_api_token_here

### Run App

``` bash
uv run streamlit run app.py
```

------------------------------------------------------------------------

## 🔧 MCP Tool Server

Run MCP server:

``` bash
uv run python mcp_server.py
```

Test with inspector:

``` bash
npx @modelcontextprotocol/inspector uv run python mcp_server.py
```

Available tools:

-   extract_text_from_pdf
-   ask_groq
-   fetch_linkedin_jobs
-   fetch_naukri_jobs

------------------------------------------------------------------------

## 📁 Project Structure

    Job_Recommender_System_with_MCP/
    │
    ├── app.py
    ├── mcp_server.py
    ├── requirements.txt
    ├── pyproject.toml
    ├── .env
    ├── .gitignore
    │
    └── src/
        ├── __init__.py
        └── helper.py

------------------------------------------------------------------------

## 📊 Results

-   Resume summary generated in seconds\
-   Skill gap analysis provided\
-   Career roadmap generated\
-   120 real-time jobs fetched

------------------------------------------------------------------------

## 📄 License

MIT License © 2026 chitaki10

------------------------------------------------------------------------

## 🙋 Contact

GitHub: https://github.com/chitaki10
