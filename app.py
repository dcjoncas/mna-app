from flask import Flask, render_template, request
import os
import json
import re
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from openai import OpenAI

load_dotenv()
print(f"✅ Using API Key: {os.getenv('OPENAI_API_KEY')[:10]}...")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RED_FLAGS = [
    "Commoditized Product/Service",
    "Overly Dependent on Owner",
    "No Proprietary Data or Process",
    "Vapor ARR / Fake Recurring Revenue",
    "Customer Churn & Bad Reviews",
    "Toxic Culture / High Turnover",
    "Highly Regulated / Legal Risks",
    "Obsolete Technology / No Upgrades",
    "Single Customer Risk",
    "Saturated Market"
]

GREEN_FLAGS = [
    "Strong Brand Recognition",
    "Loyal Customer Base",
    "Unique Technology or IP",
    "Scalable Business Model",
    "High Employee Satisfaction"
]


def ai_analyze_full(name, industry, notes, why_attractive, file_text, red_flags, green_flags):
    prompt = f"""
You are an expert M&A analyst. Here is the data collected about a potential acquisition target.  
Analyze and weigh everything: **industry, notes, why attractive, uploaded document text, red flags, green flags**.
Red flags hurt the deal, green flags help it. Include all of the following in your output:

- For each flag: analysis, why it's relevant at its score, and suggestion. Also add in suggestion for each line on how specifically "A.I." artificial intelligence can help right away e.g. AI can build a app to help by doing the following. if there is information in the description use that as a base for analysis. Call it AI HELP NOW: 
- Final recommendation: Acquire / Do Not Acquire / Proceed With Caution.
- ROI estimate in %.
- Professional summary paragraph summarizing everything.

Return ONLY valid JSON like this:
{{
"analysis": [
{{"flag":"flag name","type":"red/green","score":5,"description":"...","suggestion":"..."}},
...
],
"final_recommendation": "...",
"roi_estimate": "75%",
"summary": "..."
}}

Company Name: {name}
Industry: {industry}
Why Attractive: {why_attractive}
Notes: {notes}

Uploaded Document Content:
{file_text}

Red Flags:
{json.dumps(red_flags, indent=2)}

Green Flags:
{json.dumps(green_flags, indent=2)}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response.choices[0].message.content.strip()
        print("\n=== RAW AI RESPONSE ===\n", content)

        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
            return result
        else:
            raise ValueError("No valid JSON found in AI response.")

    except Exception as e:
        print(f"⚠️ AI parsing error: {e}")
        return {
            "analysis": [],
            "final_recommendation": "Unable to evaluate.",
            "roi_estimate": "N/A",
            "summary": "⚠️ AI failed to return a valid response.",
            "error": str(e)
        }


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        industry = request.form['industry']
        contact = request.form.get('contact', '')
        company_type = request.form['company_type']
        why_attractive = request.form.get('why_attractive', '')
        notes = request.form.get('notes', '')

        red_flags_input = []
        for i, rf in enumerate(RED_FLAGS):
            score = request.form.get(f'rf_score_{i}', '3')
            desc = request.form.get(f'rf_desc_{i}', '')
            try:
                score = int(score)
            except ValueError:
                score = 3
            red_flags_input.append({"flag": rf, "score": score, "description": desc})

        green_flags_input = []
        for i, gf in enumerate(GREEN_FLAGS):
            score = request.form.get(f'gf_score_{i}', '3')
            desc = request.form.get(f'gf_desc_{i}', '')
            try:
                score = int(score)
            except ValueError:
                score = 3
            green_flags_input.append({"flag": gf, "score": score, "description": desc})

        file_text = ""
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                ext = filename.rsplit('.', 1)[1].lower()
                try:
                    if ext == 'txt':
                        with open(filepath, 'r', errors='ignore') as f:
                            file_text = f.read()
                    elif ext == 'pdf':
                        import PyPDF2
                        with open(filepath, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            file_text = ''.join([page.extract_text() or "" for page in reader.pages])
                    elif ext == 'docx':
                        import docx
                        doc = docx.Document(filepath)
                        file_text = '\n'.join([p.text for p in doc.paragraphs])
                    elif ext == 'xlsx':
                        import pandas as pd
                        df = pd.read_excel(filepath)
                        file_text = df.to_string()
                except Exception as e:
                    print(f"⚠️ File parsing error: {e}")

        ai_result = ai_analyze_full(name, industry, notes, why_attractive, file_text, red_flags_input, green_flags_input)

        return render_template(
            'result.html',
            result=ai_result,
            company_type=company_type,
            why_attractive=why_attractive,
            file_text=file_text,
            contact=contact,
            notes=notes
        )

    return render_template('index.html', red_flags=RED_FLAGS, green_flags=GREEN_FLAGS)


@app.route('/seller_financing', methods=['GET', 'POST'])
def seller_financing():
    if request.method == 'POST':
        price = float(request.form['price'])
        down_payment_pct = float(request.form['down_payment']) / 100
        seller_financing_pct = float(request.form['seller_financing']) / 100
        interest_rate = float(request.form['interest_rate']) / 100
        amortization_years = int(request.form['amortization_years'])

        down_payment = price * down_payment_pct
        seller_note = price * seller_financing_pct
        sba_loan = price - down_payment - seller_note

        monthly_rate = interest_rate / 12
        n_months = amortization_years * 12

        if monthly_rate > 0:
            seller_payment = seller_note * (monthly_rate * (1 + monthly_rate) ** n_months) / ((1 + monthly_rate) ** n_months - 1)
        else:
            seller_payment = seller_note / n_months

        lump_sum = price
        federal_tax_pct = 0.10
        state_tax_pct = 0.05

        federal_holdback = price * federal_tax_pct
        state_holdback = price * state_tax_pct
        total_holdback = federal_holdback + state_holdback

        seller_after_tax = (down_payment + seller_note + sba_loan) - total_holdback
        lump_after_tax = price - total_holdback

        result = {
            "price": price,
            "down_payment": down_payment,
            "seller_note": seller_note,
            "sba_loan": sba_loan,
            "seller_payment": round(seller_payment, 2),
            "lump_sum": lump_sum,
            "amortization_years": amortization_years,
            "interest_rate": interest_rate * 100,
            "federal_holdback": federal_holdback,
            "state_holdback": state_holdback,
            "seller_after_tax": seller_after_tax,
            "lump_after_tax": lump_after_tax,
            "benefits": [
                "Lower upfront capital requirement",
                "Improved cash flow",
                "Potential tax advantages",
                "Stronger seller-buyer relationship",
                "Flexibility in structuring the deal"
            ]
        }

        return render_template('seller_financing_result.html', result=result)

    return render_template('seller_financing.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
