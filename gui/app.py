import os
import sys
import json
from datetime import datetime, date, timedelta

# 🔧 Ensure the root project directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.auth import authenticate_gmail
from core.analytics import load_logs, compute_stats
from core.reader import get_latest_emails
from core.summariser import summarise_email

import streamlit as st

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
LOG_PATH = os.path.join(BASE_DIR, 'sent_replies.json')

# Load or initialize config
default_config = {
    'poll_interval': 60,
    'trigger_tags': ['request', 'auto-reply', 'urgent', 'follow-up', 'meeting'],
    'spam_patterns': [r'mailer-daemon', r'no-reply'],
    'rate_limit_hours': 1
}
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
else:
    config = default_config
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

# Sidebar: Configuration & Filters
st.sidebar.header("🔧 Agent Configuration & Fetch Filters")
with st.sidebar.form(key="config_form"):
    new_poll = st.number_input("Polling interval (s)", min_value=1, value=config['poll_interval'])
    new_rate = st.number_input("Rate limit per thread (h)", min_value=0, value=config['rate_limit_hours'])
    new_triggers = st.multiselect(
        "Trigger Tags",
        options=config['trigger_tags'],
        default=config['trigger_tags']
    )
    sp_text = st.text_area(
        "Spam Patterns (one regex per line)",
        value="\n".join(config['spam_patterns']),
        height=80
    )
    include_archived = st.checkbox("Include archived emails (in:anywhere)", value=False)
    max_results = st.number_input("Max emails to fetch", min_value=5, max_value=500, value=100)
    date_input = st.date_input(
        "Date range",
        value=(date.today(), date.today())
    )
    save = st.form_submit_button("Save Settings")
    if save:
        updated = {
            'poll_interval': int(new_poll),
            'rate_limit_hours': int(new_rate),
            'trigger_tags': new_triggers,
            'spam_patterns': [line.strip() for line in sp_text.splitlines() if line.strip()]
        }
        with open(CONFIG_PATH, 'w') as f:
            json.dump(updated, f, indent=2)
        st.success("Settings saved! Restart the agent to apply.")

# Unpack date range safely
if isinstance(date_input, (list, tuple)) and len(date_input) == 2:
    start_date, end_date = date_input
else:
    start_date = end_date = date_input if isinstance(date_input, date) else date.today()

# Main UI
st.set_page_config(page_title="Email Intelligence Dashboard", layout="wide")
st.title("📬 Email Intelligence Dashboard")
st.markdown("Powered by GPT + Gmail")

# Build Gmail query
inbox = "in:anywhere" if include_archived else "in:inbox category:primary"
date_query = f"after:{start_date.strftime('%Y/%m/%d')} before:{(end_date + timedelta(days=1)).strftime('%Y/%m/%d')}"
query = f"{inbox} {date_query}"

# Fetch emails with error handling
with st.spinner("Fetching emails from Gmail..."):
    service = None
    try:
        service = authenticate_gmail()
    except Exception as auth_err:
        st.error(f"Authentication error: {auth_err}")

    emails = []
    if service:
        try:
            emails = get_latest_emails(service, max_results=max_results, query=query)
        except Exception as fetch_err:
            st.error(f"Failed to fetch emails: {fetch_err}")

# Display fetched emails
st.success(f"Loaded {len(emails)} emails from {start_date} to {end_date}.")
for email in emails:
    with st.expander(f"📧 {email.get('subject','(No subject)')}"):
        try:
            summary_data = summarise_email(email['subject'], email['body'])
        except Exception as e:
            summary_data = {'summary': f"⚠️ Summariser error: {e}", 'tags': []}
        st.markdown("### 🧠 Summary")
        st.markdown(summary_data.get('summary',''))
        st.markdown("### 🏷️ Tags")
        st.code(", ".join(summary_data.get('tags', [])))
        st.markdown("### 📨 Full Email Body")
        st.text_area(label="Content", value=email.get('body',''), height=200, disabled=True)

# Analytics Section
st.header("📊 Analytics Dashboard")
try:
    df = load_logs(LOG_PATH)
    stats = compute_stats(df)
    st.metric("Total Replies", stats['total'])
    st.subheader("Replies by Tag")
    st.bar_chart(stats['by_tag'])
    st.subheader("Replies per Day")
    st.line_chart(stats['by_day'])
except Exception as e:
    st.error(f"Analytics load error: {e}")
