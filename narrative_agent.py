import anthropic

SUMMARY_PROMPT = """
Write a 4-5 sentence executive summary for a procurement risk dashboard, in a formal
business-analyst tone, comparing {current_year} to {prior_year}.

Total spend {current_year}: INR {total_spend_current:,.0f} ({spend_change_pct}% change vs {prior_year})
Non-compliant purchase orders: {noncompliant_current} (change of {noncompliant_change} vs {prior_year})
Price variance flags: {price_variance_current} (change of {price_variance_change} vs {prior_year})
Defect rate: {defect_rate_current}% (change of {defect_rate_change} percentage points vs {prior_year})
Top vendor by spend increase: {top_mover_supplier} (+INR {top_mover_spend_increase:,.0f})

Mention the overall spend trend, flag whether compliance and quality are improving or worsening,
and name the top mover. Keep it factual and concise - do NOT invent any numbers beyond those given above.
"""

def generate_narrative(metrics: dict, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = SUMMARY_PROMPT.format(**metrics)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

if __name__ == "__main__":
    from metrics_agent import compute_metrics
    metrics = compute_metrics(current_year=2023, prior_year=2022)

    # Paste your own Anthropic API key here, or set it as an environment variable
    API_KEY = "YOUR_API_KEY_HERE"

    narrative = generate_narrative(metrics, API_KEY)
    print(narrative)
