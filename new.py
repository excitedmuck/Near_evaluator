import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
if not client.api_key:
    raise ValueError("Please set OPENAI_API_KEY environment variable")

# Perplexity API configuration
PPLX_API_KEY = os.getenv("PPLX_API_KEY")
PPLX_API_URL = "https://api.perplexity.ai/chat/completions"

def scrape_near_forum(url):
    """Scrape content from a NEAR governance forum post."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the title - it's in the first link inside topic-title
        title_elem = soup.select_one('#topic-title h1 a')
        print("Found title element:", title_elem)
        title = title_elem.get_text(strip=True) if title_elem else 'Untitled Proposal'
        print("Extracted title:", title)
        
        # Find the main post content
        post_content = soup.find('div', class_='post')
        if not post_content:
            return {'error': 'Could not find post content'}
        
        # Extract text content
        content = post_content.get_text(separator='\n', strip=True)
        
        return {'title': title, 'content': content, 'url': url}
    except Exception as e:
        return {'error': str(e)}

def get_perplexity_analysis(content):
    """Get Perplexity AI analysis of the proposal."""
    headers = {
        "Authorization": f"Bearer {PPLX_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "sonar-pro",  # Using the model from deep_perplexity.py
        "messages": [
            {
                "role": "system",
                "content": "You are a NEAR governance evaluator based on your current and historic knowledge of NEAR ecosystem."
            },
            {
                "role": "user",
                "content": f"Give a short analysis of how this proposal compares to others, and whether it is needed/comprehensive, dont add any footnotes: {content}"
            }
        ],
        "max_tokens": 2000,  # Increased max tokens for more detailed analysis
        "temperature": 0.7
    }
    
    try:
        response = requests.post(PPLX_API_URL, headers=headers, json=data)
        if response.status_code != 200:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return f"Error: Could not get ecosystem analysis (HTTP {response.status_code})"
        
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return f"Error getting Perplexity analysis: {str(e)}"

def analyze_proposal(content):
    """Analyze a proposal using GPT-4."""
    try:
        system_message = """You are an expert reviewer for NEAR Protocol governance proposals. Analyze proposals using these criteria, adapting to proposal type (e.g., technical, community, infrastructure):

1. Writing Quality (20%):
   - Professional tone, correct grammar, no jargon, clear structure.
   - Score 0-4 (0=incoherent, 1=poor with errors, 2=acceptable, 3=professional, 4=exceptional).
2. Proposal Clarity (30%):
   - SMART objectives (Specific, Measurable, Achievable, Relevant, Time-bound).
   - Score 0-4 (0=unclear, 1=vague, 2=partially clear, 3=clear, 4=highly detailed).
3. Key Elements (40% for budget/timelines, 10% for team):
   - Required: budget (cost breakdown), team (roles, experience), goals, context, milestones, timelines, KPIs.
   - Score 0-4 (0=missing most, 1=few present, 2=some present, 3=most present, 4=all present with detail).
   - For incomplete elements, note feasibility or need for clarification.

Return a JSON with this EXACT structure (no additional fields):
{
    "writing_quality": {
        "status": "PASS",
        "score": 3,
        "explanation": "Brief explanation",
        "supporting_quotes": ["quote 1", "quote 2"]
    },
    "proposal_clarity": {
        "status": "PASS",
        "score": 3,
        "explanation": "Brief explanation",
        "supporting_quotes": ["quote 1", "quote 2"]
    },
    "key_elements": {
        "status": "PASS",
        "score": 3,
        "explanation": "Brief explanation",
        "elements_found": ["element 1", "element 2"],
        "elements_missing": ["element 1", "element 2"],
        "comments": ["comment 1", "comment 2"]
    },
    "weighted_score": 3
}"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Please analyze this proposal and return ONLY the JSON response with no additional text or formatting:\n\n{content}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        if not response_text:
            st.error("Error: Empty response from OpenAI")
            return None
            
        try:
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as e:
            st.error(f"Error parsing OpenAI response as JSON: {str(e)}\n\nResponse text: {response_text[:200]}...")
            return None
            
    except Exception as e:
        st.error(f"Error analyzing proposal: {str(e)}")
        return None

def display_analysis_results(analysis, title):
    """Display analysis results in a structured way using Streamlit."""
    if not analysis:
        return
        
    # Display title
    st.title(title)

    # Create three columns for the main metrics
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    # Overall Score
    with col1:
        weighted_score = analysis.get('weighted_score', 0)
        st.metric("Overall Score", f"{weighted_score:.2f}/4")
    
    # Writing Quality Score
    with col2:
        wq_score = analysis['writing_quality']['score']
        wq_status = analysis['writing_quality']['status']
        st.metric("Writing", f"{wq_score}/4", delta="PASS" if wq_status == "PASS" else "FAIL")
    
    # Proposal Clarity Score
    with col3:
        pc_score = analysis['proposal_clarity']['score']
        pc_status = analysis['proposal_clarity']['status']
        st.metric("Clarity", f"{pc_score}/4", delta="PASS" if pc_status == "PASS" else "FAIL")
    
    # Key Elements Score
    with col4:
        ke_score = analysis['key_elements']['score']
        ke_status = analysis['key_elements']['status']
        st.metric("Elements", f"{ke_score}/4", delta="PASS" if ke_status == "PASS" else "FAIL")
    
    # Tabs for detailed analysis
    tab1, tab2, tab3 = st.tabs(["Writing Quality", "Proposal Clarity", "Key Elements"])
    
    # Writing Quality Tab
    with tab1:
        st.write(analysis['writing_quality']['explanation'])
        if analysis['writing_quality']['supporting_quotes']:
            with st.expander("Supporting Quotes"):
                for quote in analysis['writing_quality']['supporting_quotes']:
                    st.info(quote)
    
    # Proposal Clarity Tab
    with tab2:
        st.write(analysis['proposal_clarity']['explanation'])
        if analysis['proposal_clarity']['supporting_quotes']:
            with st.expander("Supporting Quotes"):
                for quote in analysis['proposal_clarity']['supporting_quotes']:
                    st.info(quote)
    
    # Key Elements Tab
    with tab3:
        st.write(analysis['key_elements']['explanation'])
        
        # Two columns for found and missing elements
        col1, col2 = st.columns(2)
        with col1:
            if analysis['key_elements']['elements_found']:
                st.markdown("### Found")
                for element in analysis['key_elements']['elements_found']:
                    st.success(f"✅ {element}")
        with col2:
            if analysis['key_elements']['elements_missing']:
                st.markdown("### Missing")
                for element in analysis['key_elements']['elements_missing']:
                    st.warning(f"⚠️ {element}")
        
        if analysis['key_elements']['comments']:
            with st.expander("Additional Comments"):
                for comment in analysis['key_elements']['comments']:
                    st.info(comment)
    
    # Download button in sidebar
    with st.sidebar:
        st.download_button(
            label="⬇️ Download Analysis as JSON",
            data=json.dumps(analysis, indent=2),
            file_name=f"proposal_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

def main():
    st.set_page_config(page_title="NEAR Proposal Analyzer", layout="wide")
    st.title("NEAR Proposal Analyzer")
    st.write("Enter a NEAR governance forum URL to analyze the proposal.")
    
    # URL input
    url = st.text_input("Enter NEAR Forum URL", "https://gov.near.org/t/rejected-proposal-for-near-maps-nft-onboarding-campaign/37599")
    
    if st.button("Analyze Proposal"):
        with st.spinner("Scraping proposal content..."):
            result = scrape_near_forum(url)
            
            if 'error' in result:
                st.error(f"Error scraping proposal: {result['error']}")
            else:
                st.success("✅ Proposal content scraped successfully!")
                
                # Show raw content in expander
                with st.expander("View Raw Content"):
                    st.write(result['content'])
                
                # Analyze the proposal with GPT-4
                with st.spinner("Analyzing proposal with GPT-4..."):
                    analysis = analyze_proposal(result['content'])
                    if analysis:
                        display_analysis_results(analysis, result['title'])
                
                # Get Perplexity ecosystem analysis
                with st.spinner("Getting NEAR ecosystem analysis..."):
                    st.markdown("### NEAR Ecosystem Analysis")
                    pplx_analysis = get_perplexity_analysis(result['content'])
                    st.write(pplx_analysis)

if __name__ == "__main__":
    main()
