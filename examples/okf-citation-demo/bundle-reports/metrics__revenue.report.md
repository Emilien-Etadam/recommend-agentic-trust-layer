# Verification report — Revenue

*recommend-trust-layer/0.1 · 2026-07-29T18:25:15Z · mode: citation-integrity (bundle sources as evidence)*

**Outcome: FAILED**

- **contradicts** · `[^revenue-policy]` — Revenue for a fiscal year is the sum of net_amount over orders that (a) reached order_status = 'delivered', (b) completed the 30-day return window, and (c) fall in the fiscal year by order_ts. Multi-currency orders are converted to USD at the order_ts daily reference rate.
  - The claim incorrectly states that multi-currency orders are converted at the order date rate, whereas the policy explicitly mandates using the delivery date rate. | challenged: The claim incorrectly specifies the conversion date as 'order_ts', whereas the policy explicitly mandates using the 'delive
  - evidence quote: “Multi-currency orders are converted at the daily reference rate published in finance.fx_daily_rates, using the DELIVERY date (delivered_ts), not the order date.”
- **contradicts** · `[^revenue-policy]` — Orders with net_amount below $1.00 are exempt from recognition and booked directly to promotional expense.
  - The Revenue Recognition Policy defines the recognized amount as the net_amount without any mention of an exemption threshold for orders below $1.00 or a policy to book such orders to promotional expense.
  - evidence quote: “The recognized amount for an order equals net_amount = gross_amount - discount_amount.”
- **contradicts** · `[^(uncited)]` — **By fiscal year:** the sanctioned computation takes year as its sole parameter.
  - [uncited claim] The evidence explicitly states that fiscal-year metrics are calculated using the order timestamp (order_ts), not just a year parameter. | challenged: The evidence explicitly states in the 'Fiscal year' section that 'All fiscal-year metrics use fiscal_year = EXTRACT(YEAR FROM order_ts)', which direct
  - evidence quote: “All fiscal-year metrics use `fiscal_year = EXTRACT(YEAR FROM order_ts)`.”
- **no-evidence** · `[^(uncited)]` — **By channel or category:** these are approved narrations, not new metrics. Join the receipt's row-level result to orders.channel or to order_lines × products.category client-side. Do NOT rewrite the sanctioned SQL.
  - [uncited claim] The provided evidence is a revenue recognition policy document that defines accounting triggers and calculations, but it contains no information regarding channel or category reporting, client-side joins, or SQL implementation instructions.
- **no-evidence** · `[^(uncited)]` — **Verified:** VP Finance sign-off on 2026-07-01, against the FY2026 policy.
  - [uncited claim] The provided evidence defines the FY2026 Revenue Recognition Policy but contains no record, log, or attestation confirming that the VP of Finance signed off on the policy on 2026-07-01.
- **related-only** · `[^(uncited)]` — **Stale after 2026-12-31:** Finance re-issues the revenue recognition policy each January. Consumers of this concept after 2027-01-01 MUST re-verify the definition against the new policy before serving.
  - [uncited claim] The provided evidence confirms the policy is scheduled for review on 2026-12-31, but it contains no information regarding a mandatory annual re-issuance process in January or a requirement for users to re-verify the definition after 2027-01-01.
  - evidence quote: “Next scheduled review: 2026-12-31”
