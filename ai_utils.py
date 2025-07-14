from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# Load .env file
load_dotenv()

# Get API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_target(name, industry, contact, notes, company_type, why_attractive, file_text, red_flags_input):
    rf_text = "\n".join([
        f"- {rf['flag']}: score {rf['score']}, description: {rf['description']}"
        for rf in red_flags_input
    ])

    prompt = f"""
You are an expert M&A analyst. Below is company information, uploaded document, and user-provided scores & descriptions for 10 Red Flags.
Analyze the Red Flags, validate or adjust if needed, and suggest actionable recommendations.

Return JSON in this format and nothing else:
{{
  "red_flags_analysis": [
    {{"flag": "...", "score": 3, "description": "...", "ai_suggestion": "..."}},
    …
  ],
  "recommendation": "..."
}}

## Company Info
Name: {name}
Industry: {industry}
Contact: {contact}
Notes: {notes}
Company Type: {company_type}
Why Attractive: {why_attractive}

## Red Flags Provided
{rf_text}

## Uploaded Document
{file_text}
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except Exception as e:
        print("\n--- RAW AI OUTPUT ---\n")
        print(content)
        print("\n--- ERROR ---\n", e)
        return {
            "red_flags_analysis": [],
            "recommendation": "⚠️ Could not parse response. Check AI output."
        }


def analyze_airoi(company_type, why_attractive):
    prompt = f"""
You are an expert M&A and AI consultant.
For a target company of type: {company_type}, which is attractive because: {why_attractive},
explain how AI can improve efficiencies and operations if acquired.

Output JSON only in this format:
{{
  "ai_efficiency_areas": [
    {{"area": "...", "score": 4, "notes": "..."}},
    …
  ],
  "percentage_breakdown": {{
    "Poor": "10%",
    "Good": "30%",
    "Very Good": "40%",
    "Excellent": "20%"
  }},
  "summary": "..."
}}
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except Exception as e:
        print("\n--- RAW AIROI OUTPUT ---\n")
        print(content)
        print("\n--- ERROR ---\n", e)
        return {
            "ai_efficiency_areas": [],
            "percentage_breakdown": {},
            "summary": "⚠️ Could not parse AIROI response."
        }
