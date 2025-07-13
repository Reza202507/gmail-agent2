
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def tag_email_tags(subject: str, body: str) -> list:
    """Use GPT to tag emails based on subject and body."""
    prompt = f"""You are an intelligent email classifier. Based on the following subject and body, return 1 to 3 suitable tags from this list:
["urgent", "meeting", "follow-up", "request", "auto-reply", "thank you", "complaint", "feedback", "newsletter", "social", "promotion", "invoice", "personal"]

Subject: {subject}
Body: {body}

Return tags as a Python list. If no tag fits, return ["Miscellaneous"].
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    tags = eval(response.choices[0].message.content.strip())
    return tags

def generate_tags(email_subject: str, email_body: str, max_tags: int = 5) -> list:
    """Generate semantic tags for an email using GPT."""
    tags = tag_email_tags(email_subject, email_body)
    return tags[:max_tags]
