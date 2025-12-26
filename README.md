# 🚀 Smart AI Data Profiler & Automation Pipeline

### **Overview**
A cloud-native intelligent system built to automate data profiling and cleaning. This tool uses **Gemini 2.5 AI** to transform raw CSV data into structured insights and pushes them to automated workflows via **Webhooks**.

### **🛠️ Technical Stack**
* **AI Engine:** Google Gemini 2.5 Flash
* **Web Interface:** Streamlit (Cloud-deployed)
* **Data Handling:** Pandas & JSON
* **Automation:** REST API Webhook integration

### **✨ Key Features**
* **Zero-Touch Cleaning:** AI automatically detects and fixes data inconsistencies.
* **JSON Webhook Output:** Instantly sends results to platforms like **n8n** or **Zapier**.
* **Cloud Security:** Implements secure environment variable management.

### **🚀 Setup for Recruiters**
1. Install dependencies: `pip install -r requirements.txt`
2. **Security Note:** This app requires a `GEMINI_API_KEY`. In Streamlit Cloud, add this under **Settings > Secrets**.
