import os
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import logging
from dotenv import load_dotenv
from google import genai

# --- 0. PROFESSIONAL LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()] # Removed FileHandler for Cloud compatibility
)
logger = logging.getLogger(__name__)

# --- 1. CONFIGURATION AND INITIALIZATION ---
load_dotenv()

# FIX: Support for both local (.env) and Streamlit Cloud (Secrets)
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("🚨 CRITICAL ERROR: GEMINI_API_KEY not found. Please add it to Streamlit Secrets.")
    st.stop() 

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Initialization Failure: {e}")
    st.error(f"❌ Failed to initialize Gemini Client: {e}")
    st.stop()

# --- 2. UTILITY FUNCTIONS ---

def generate_llm_prompt(df: pd.DataFrame) -> str:
    """Creates a detailed system instruction and data summary for the LLM Agent."""
    initial_summary = df.head(5).to_markdown(index=False)
    dtype_summary = df.dtypes.to_frame(name='Dtype').to_markdown()
    missing_data = df.isnull().sum()
    missing_pct = (missing_data[missing_data > 0] / len(df) * 100).round(2)
    missing_summary = missing_pct.to_frame(name='Missing_Percentage').to_markdown()

    return f"""
You are an expert Data Profiler and Python Data Cleaning Agent.
Your task is to analyze the data and generate a single Python code block to clean the DataFrame named 'df'.

STRUCTURE:
1. **RATIONALE:** Detailed markdown report on data issues.
2. **CODE BLOCK:** One Python block starting with ```python and ending with ```.

DATA SUMMARY:
{initial_summary}

DTYPES:
{dtype_summary}

MISSING DATA:
{missing_summary}
"""

def extract_code(text: str) -> str:
    try:
        return text.split("```python")[1].split("```")[0].strip()
    except:
        return ""

def extract_report(text: str) -> str:
    if "RATIONALE:" in text:
        return text.split("```python")[0].strip()
    return "Report generated successfully. Review the code below."

def send_to_webhook(dataframe, webhook_url):
    try:
        data_json = dataframe.head(100).to_dict(orient='records')
        payload = {
            "source": "Smart Data Profiler App",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": data_json
        }
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return False

# --- 3. STREAMLIT APPLICATION LAYOUT ---

st.set_page_config(page_title="Smart Data Profiler", layout="wide")
st.title("🧠 Smart Data Profiler & Cleanser (Gemini Agent)")
st.caption("Automated data quality assessment and workflow integration for AI Automation Associates.")

uploaded_file = st.file_uploader("📂 Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Use session state to prevent reloading data on every click
    if 'df_original' not in st.session_state:
        st.session_state['df_original'] = pd.read_csv(uploaded_file)
    
    st.subheader("1. Original Data Sample")
    st.dataframe(st.session_state['df_original'].head(10))

    if st.button("✨ Analyze & Generate Cleaning Plan"):
        logger.info("Starting AI Analysis Pipeline...")
        prompt = generate_llm_prompt(st.session_state['df_original'])

        with st.spinner('🤖 AI Agent is analyzing the data...'):
            try:
                # FIX: Using the most stable model name
                response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                
                if not response.text:
                    st.error("⚠️ AI response blocked or empty.")
                    st.stop()
                
                cleaning_code = extract_code(response.text)
                report_text = extract_report(response.text)

                # Safe Execution of AI-generated code
                df_clean = st.session_state['df_original'].copy()
                exec(cleaning_code, {'pd': pd, 'np': np, 'df': df_clean})
                
                # Update Session State
                st.session_state['df_clean'] = df_clean
                st.session_state['report_text'] = report_text
                st.session_state['cleaning_code'] = cleaning_code
                logger.info("Pipeline successful.")

            except Exception as e:
                logger.error(f"Pipeline failure: {e}")
                st.error(f"❌ AI Processing Error: {e}")

    # --- RESULTS DISPLAY ---
    if 'df_clean' in st.session_state:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("2. AI Rationale")
            st.markdown(st.session_state['report_text'])
        with col2:
            st.subheader("3. Generated Code")
            st.code(st.session_state['cleaning_code'], language='python')
        
        st.subheader("4. Cleaned Data Preview")
        st.dataframe(st.session_state['df_clean'].head(10))
        
        csv = st.session_state['df_clean'].to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Cleaned CSV", csv, "cleaned_data.csv", "text/csv")

        st.divider()
        st.subheader("🚀 5. Automation Workflow")
        webhook_url = st.text_input("Enter Webhook URL (Webhook.site, n8n, Zapier):")

        if st.button("📤 Trigger Automation Pipeline"):
            if webhook_url:
                if send_to_webhook(st.session_state['df_clean'], webhook_url):
                    st.success("✅ Data successfully sent to automation pipeline!")
                else:
                    st.error("❌ Webhook delivery failed. Check URL or logs.")
            else:
                st.warning("Please provide a Webhook URL first.")
