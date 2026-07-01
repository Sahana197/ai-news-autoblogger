import streamlit as st
import requests
import smtplib
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI News Auto-Blogger",
    page_icon="📰",
    layout="wide"
)

# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #f8fafc;
    color: #1e293b;
}
.stApp { background-color: #f8fafc; }

.main-title {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.2rem;
}
.subtitle {
    color: #64748b;
    font-size: 0.92rem;
    margin-bottom: 1.5rem;
}
.badge {
    background: #3b82f6;
    color: #fff;
    border-radius: 50%;
    width: 26px;
    height: 26px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.78rem;
    font-weight: 700;
    margin-right: 8px;
}
.news-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px 18px;
    margin: 10px 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.news-title {
    font-weight: 600;
    font-size: 0.97rem;
    color: #1e293b;
    margin-bottom: 4px;
}
.news-meta {
    font-size: 0.78rem;
    color: #94a3b8;
    margin-bottom: 6px;
}
.news-snippet {
    font-size: 0.87rem;
    color: #475569;
    line-height: 1.6;
}
.blog-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 32px;
    margin: 16px 0;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.blog-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    font-weight: 900;
    color: #1e293b;
    margin-bottom: 8px;
    line-height: 1.3;
}
.blog-meta {
    font-size: 0.8rem;
    color: #94a3b8;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f1f5f9;
}
.success-box {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 8px;
    padding: 12px 16px;
    color: #166534;
    font-weight: 500;
    font-size: 0.9rem;
}
.stButton > button {
    background: #3b82f6;
    color: #fff;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.4rem;
    font-family: 'Inter', sans-serif;
    transition: background 0.2s;
}
.stButton > button:hover { background: #2563eb; }
section[data-testid="stSidebar"] {
    background: #fff;
    border-right: 1px solid #e2e8f0;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
for key in ["articles", "blog_title", "blog_body", "blog_html"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "articles" else None

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ API Keys")
    st.markdown("---")
    news_api_key = st.text_input("📰 NewsAPI Key", type="password", placeholder="newsapi.org → free key")
    groq_api_key = st.text_input("🔑 Groq API Key", type="password", placeholder="console.groq.com")

    st.markdown("---")
    st.markdown("### 🔍 Search Settings")
    topic        = st.text_input("Topic", value="Artificial Intelligence")
    num_articles = st.slider("Number of articles", 3, 10, 5)
    language     = st.selectbox("Language", ["en", "hi", "fr", "de"], index=0)

    st.markdown("---")
    st.markdown("### 📧 Email *(optional)*")
    sender_email    = st.text_input("Your Gmail", placeholder="you@gmail.com")
    sender_password = st.text_input("App Password", type="password",
                                    help="Google Account → Security → App Passwords")
    receiver_email  = st.text_input("Send To", placeholder="receiver@email.com")

    st.markdown("---")
    if st.button("🗑️ Reset All"):
        for key in ["articles", "blog_title", "blog_body", "blog_html"]:
            st.session_state[key] = [] if key == "articles" else None
        st.rerun()

# ─────────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────────
def fetch_news(topic, num, language, api_key):
    resp = requests.get(
        "https://newsapi.org/v2/everything",
        params={"q": topic, "language": language, "pageSize": num,
                "sortBy": "publishedAt", "apiKey": api_key},
        timeout=15
    )
    if resp.status_code != 200:
        return None, f"NewsAPI Error {resp.status_code}: {resp.json().get('message', '')}"
    articles = []
    for a in resp.json().get("articles", []):
        if a.get("title") and a["title"] != "[Removed]":
            articles.append({
                "title":       a.get("title", ""),
                "description": a.get("description", "") or "",
                "source":      a.get("source", {}).get("name", ""),
                "publishedAt": a.get("publishedAt", "")[:10],
                "url":         a.get("url", "")
            })
    return articles, None

def generate_blog(articles, topic, api_key):
    news_text = ""
    for i, a in enumerate(articles, 1):
        news_text += f"{i}. {a['title']}\n{a['description']}\nSource: {a['source']} ({a['publishedAt']})\n\n"

    prompt = f"""You are a professional tech blogger. Based on these latest news articles about "{topic}":

{news_text}

Write a well-structured, engaging blog post that:
1. First line must be: TITLE: [your compelling title]
2. Hook introduction paragraph
3. 3-4 key sections with ## subheadings
4. Each section 2-3 paragraphs
5. Forward-looking conclusion
6. 600-800 words total
7. Smart, conversational tone

Start with TITLE: on the very first line."""

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.7, "max_tokens": 1500},
        timeout=60
    )
    if resp.status_code != 200:
        return None, None, f"Groq Error {resp.status_code}"

    full  = resp.json()["choices"][0]["message"]["content"].strip()
    title = topic
    body  = full
    if full.startswith("TITLE:"):
        lines = full.split("\n", 1)
        title = lines[0].replace("TITLE:", "").strip()
        body  = lines[1].strip() if len(lines) > 1 else full
    return title, body, None

def render_body_html(body, inline=False):
    """Render blog body as HTML. inline=True for email, False for Streamlit display."""
    html = ""
    for row in body.split("\n"):
        row = row.strip()
        if not row:
            html += "<br>"
        elif row.startswith("## "):
            style = "font-family:Georgia,serif;font-size:1.15rem;font-weight:700;color:#1e293b;margin:20px 0 8px;"
            html += f"<h2 style='{style}'>{row[3:]}</h2>"
        elif row.startswith("# "):
            style = "font-family:Georgia,serif;font-size:1.4rem;font-weight:900;color:#1e293b;"
            html += f"<h1 style='{style}'>{row[2:]}</h1>"
        else:
            style = "font-size:0.96rem;line-height:1.8;color:#334155;margin-bottom:12px;"
            html += f"<p style='{style}'>{row}</p>"
    return html

def blog_to_email_html(title, body, topic):
    return f"""<html><body style='max-width:680px;margin:40px auto;font-family:Inter,sans-serif;background:#f8fafc;padding:40px;border-radius:12px;'>
<h1 style='font-family:Georgia,serif;font-size:2rem;font-weight:900;color:#1e293b;line-height:1.2;margin-bottom:8px;'>{title}</h1>
<p style='color:#94a3b8;font-size:0.82rem;margin-bottom:24px;'>
    AI Generated &bull; {datetime.now().strftime('%B %d, %Y')} &bull; Topic: {topic}
</p>
<hr style='border:none;border-top:2px solid #e2e8f0;margin-bottom:24px;'>
{render_body_html(body, inline=True)}
<hr style='border:none;border-top:1px solid #e2e8f0;margin-top:32px;'>
<p style='color:#cbd5e1;font-size:0.75rem;'>Auto-generated using Groq LLM + NewsAPI</p>
</body></html>"""

def send_email(sender, password, receiver, subject, html_content):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = receiver
    msg.attach(MIMEText(html_content, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())

# ─────────────────────────────────────────────
#  MAIN UI
# ─────────────────────────────────────────────
st.markdown('<div class="main-title">📰 AI News Auto-Blogger</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Fetch latest news → Generate blog with Groq → Download or Send via Email</div>', unsafe_allow_html=True)

# ── STEP 1 ────────────────────────────────────
st.markdown("### <span class='badge'>1</span> Fetch Latest News", unsafe_allow_html=True)

if st.button("🔍 Fetch News Articles"):
    if not news_api_key:
        st.error("⚠️ Enter your NewsAPI key in the sidebar.")
    else:
        with st.spinner(f"Fetching news about '{topic}'..."):
            articles, err = fetch_news(topic, num_articles, language, news_api_key)
        if err:
            st.error(f"❌ {err}")
        else:
            st.session_state.articles   = articles
            st.session_state.blog_title = None
            st.session_state.blog_body  = None
            st.session_state.blog_html  = None
            st.success(f"✅ Fetched {len(articles)} articles!")

if st.session_state.articles:
    for a in st.session_state.articles:
        st.markdown(f"""
        <div class="news-card">
            <div class="news-title">{a['title']}</div>
            <div class="news-meta">📰 {a['source']} &nbsp;•&nbsp; 🗓️ {a['publishedAt']}</div>
            <div class="news-snippet">{a['description']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── STEP 2 ────────────────────────────────
    st.markdown("### <span class='badge'>2</span> Generate Blog Post", unsafe_allow_html=True)

    if st.button("✍️ Generate Blog with Groq"):
        if not groq_api_key:
            st.error("⚠️ Enter your Groq API key in the sidebar.")
        else:
            with st.spinner("Writing your blog post..."):
                title, body, err = generate_blog(st.session_state.articles, topic, groq_api_key)
            if err:
                st.error(f"❌ {err}")
            else:
                st.session_state.blog_title = title
                st.session_state.blog_body  = body
                st.session_state.blog_html  = blog_to_email_html(title, body, topic)
                st.success("✅ Blog generated!")

if st.session_state.blog_body:
    st.markdown(f"""
    <div class="blog-card">
        <div class="blog-title">{st.session_state.blog_title}</div>
        <div class="blog-meta">✍️ AI Generated &nbsp;•&nbsp; 📅 {datetime.now().strftime('%B %d, %Y')} &nbsp;•&nbsp; 🏷️ {topic}</div>
        <div>{render_body_html(st.session_state.blog_body)}</div>
    </div>
    """, unsafe_allow_html=True)

    st.download_button(
        "⬇️ Download Blog as HTML",
        data=st.session_state.blog_html,
        file_name=f"blog_{datetime.now().strftime('%Y%m%d')}.html",
        mime="text/html"
    )

    st.markdown("---")

    # ── STEP 3 ────────────────────────────────
    st.markdown("### <span class='badge'>3</span> Send via Email *(optional)*", unsafe_allow_html=True)

    if st.button("📧 Send Blog via Email"):
        if not all([sender_email, sender_password, receiver_email]):
            st.warning("⚠️ Fill in all email fields in the sidebar.")
        else:
            with st.spinner("Sending..."):
                try:
                    send_email(
                        sender_email, sender_password, receiver_email,
                        f"📰 AI Blog: {st.session_state.blog_title}",
                        st.session_state.blog_html
                    )
                    st.markdown(f'<div class="success-box">✅ Blog sent to {receiver_email}!</div>',
                                unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Email failed: {e}\n\n💡 Use Gmail App Password, not your main password.")

else:
    if not st.session_state.articles:
        st.markdown("""
        <div style="text-align:center;padding:70px 20px;color:#94a3b8;">
            <div style="font-size:3rem;">📰</div>
            <h3 style="color:#64748b;">Add your API keys in the sidebar and click Fetch!</h3>
            <p>Get a free NewsAPI key at <strong>newsapi.org</strong></p>
        </div>
        """, unsafe_allow_html=True)