import anthropic, os, json
from .base import LLMBackend

PROMPT_TEMPLATE = """You are a document classifier for an EU worker posting company.
Classify the document text below into exactly one category:
identity_document | employment_contract | payslip | invoice | tax_form | other

Then extract the relevant key fields as JSON.

Fields to extract per category:
- identity_document: full_name, date_of_birth, document_number, expiry_date, nationality
- employment_contract: employee_name, employer, start_date, job_title, salary
- payslip: employee_name, employer, period, gross_salary, net_salary
- invoice: issuer, recipient, total_amount, date, invoice_number
- tax_form: taxpayer_name, fiscal_code, tax_year, total_income, tax_withheld
- other: (return empty dict)

Respond ONLY with valid JSON:
{{"category": "...", "extracted_fields": {{...}}}}

Document text:
{text}"""

class RemoteLLM(LLMBackend):
    def classify(self, text: str) -> dict:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(text=text[:4000])}]
        )
        return json.loads(msg.content[0].text)