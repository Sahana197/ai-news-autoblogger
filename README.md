
# AI News Auto-Blogger

An automated news-to-blog generation system that fetches real-time articles via NewsAPI and transforms them into professional blog posts using Groq's Llama-3.3-70B LLM.

## Features

- Fetch latest news from NewsAPI
- Generate AI-powered blogs using Groq LLM
- Download blogs as HTML files
- Send blogs via email (Gmail SMTP)

## Tech Stack

- Streamlit (Frontend)
- Python 3.8+
- Groq API (Llama-3.3-70B)
- NewsAPI
- Gmail SMTP

## How to Get API Keys

### 1. NewsAPI Key

1. Go to newsapi.org/register
2. Create a free account
3. Copy your API key from the dashboard

### 2. Groq API Key

1. Go to console.groq.com
2. Sign up for a free account
3. Navigate to "API Keys" section
4. Click "Create API Key"
5. Copy the generated key

### 3. Gmail App Password (Optional - for email feature)

1. Go to your Google Account > Security
2. Enable 2-Step Verification
3. Search for "App Passwords"
4. Select: App = Mail, Device = Other
5. Generate and copy the 16-character password

## How to Run Locally

**Step 1: Clone the Repository**

```bash
git clone https://github.com/Sahana197/ai-news-autoblogger.git
cd ai-news-autoblogger
```

**Step 2: Install Dependencies**

```bash
pip install -r requirements.txt
```

**Step 3: Run the Application**

```bash
streamlit run app.py
```

The app will open at http://localhost:8501

**Step 4: Enter API Keys**

- In the sidebar, paste your NewsAPI key
- Paste your Groq API key
- The app is now ready to use
