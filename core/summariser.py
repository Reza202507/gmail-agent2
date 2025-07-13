import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("GPT_MODEL", "gpt-3.5-turbo")


def summarise_email(subject, body):
    if not body:
        return {"summary": "⚠️ No content to summarise.", "tags": ["Unclassified"]}

    prompt = f"""
You are a professional email assistant.

Your task is to:
1. Summarise the following email in 2–3 concise bullet points.
2. Provide 1–3 relevant classification tags (like "Meeting", "Invoice", "Urgent", "FYI", etc.).

Respond in this format exactly:
Summary:
• ...
• ...
Tags:
[ "Tag1", "Tag2" ]
    
Email Subject: {subject}

Email Body:
{body}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a professional summariser and classifier for emails."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=600
        )
        content = response.choices[0].message.content

        # Simple parsing logic
        summary_section = content.split("Tags:")[0].strip()
        tags_section = content.split("Tags:")[1].strip()

        summary = summary_section.replace("Summary:", "").strip()
        tags = eval(tags_section) if tags_section.startswith("[") else ["Unclassified"]

        return {
            "summary": summary,
            "tags": tags
        }

    except Exception as e:
        return {
            "summary": f"⚠️ GPT Error: {str(e)}",
            "tags": ["Error"]
        }
