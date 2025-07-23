# NEAR Proposal Analyzer

A Streamlit web application that analyzes NEAR governance forum proposals using OpenAI GPT-4 and Perplexity AI.

## Features

- Scrapes proposal content from NEAR governance forum URLs
- Extracts proposal title and main content
- Analyzes proposals using GPT-4 with detailed scoring criteria:
  - Writing Quality
  - Proposal Clarity
  - Key Elements
- Provides ecosystem analysis using Perplexity AI
- Interactive UI with expandable sections and downloadable results

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env`:
   ```
   OPENAI_API_KEY=your_openai_api_key
   PPLX_API_KEY=your_perplexity_api_key
   ```

## Running Locally

```bash
streamlit run new.py
```

## Deployment

This app can be deployed to Streamlit Cloud:

1. Push to GitHub
2. Connect to Streamlit Cloud
3. Add environment variables in Streamlit Cloud settings
4. Deploy!
