# Verification report — Customer Orders

*recommend-trust-layer/0.1 · 2026-07-29T18:25:15Z · mode: citation-integrity (bundle sources as evidence)*

**Outcome: FAILED**

- **unverifiable** · `[^warehouse-schema]` — order_id — STRING — Globally unique order id. Generated at order creation.
  - source 'Acme Retail warehouse schema — sales dataset' could not be read
- **unverifiable** · `[^warehouse-schema]` — customer_id — STRING — FK into customers. Never null for completed orders.
  - source 'Acme Retail warehouse schema — sales dataset' could not be read
- **supports** · `[^revenue-policy]` — order_ts — TIMESTAMP — Order placement time in UTC. This is the timestamp used for fiscal-year assignment.
  - The Revenue Recognition Policy explicitly states that all fiscal-year metrics use the order_ts timestamp to determine the fiscal year.
  - evidence quote: “All fiscal-year metrics use `fiscal_year = EXTRACT(YEAR FROM order_ts)`.”
- **related-only** · `[^revenue-policy]` — order_status — STRING — One of pending, paid, shipped, delivered, cancelled, refunded. Revenue is recognized only when order_status = 'delivered' and the 30-day return window has closed.
  - [source only partially states this] While the source confirms the revenue recognition criteria, it does not define the 'order_status' string or list the specific set of possible values (pending, paid, shipped, etc.).
  - evidence quote: “Revenue is recognized when a customer order reaches `order_status = 'delivered'` **and** the return window has closed (delivered date + 30 days).”
- **unverifiable** · `[^warehouse-schema]` — gross_amount — NUMERIC(18,4) — Pre-discount subtotal, in currency. Excludes tax and shipping.
  - source 'Acme Retail warehouse schema — sales dataset' could not be read
- **related-only** · `[^revenue-policy]` — discount_amount — NUMERIC(18,4) — Total discounts applied (promo codes, loyalty credits, price adjustments).
  - [source only partially states this] The source defines 'discount_amount' as a component of the 'net_amount' calculation, but it does not specify the data type (NUMERIC(18,4)) or explicitly list the examples of discounts provided in the claim. | challenged: The policy defines 'discount_amount' as a c
  - evidence quote: “The recognized amount for an order equals `net_amount = gross_amount - discount_amount`.”
- **contradicts** · `[^revenue-policy]` — net_amount — NUMERIC(18,4) — gross_amount + tax_amount. This is the recognized-revenue amount per policy.
  - The policy explicitly defines net_amount as 'gross_amount - discount_amount' and states that tax is excluded from revenue, directly contradicting the claim that net_amount includes tax.
  - evidence quote: “The recognized amount for an order equals net_amount = gross_amount - discount_amount. Shipping and tax are excluded from revenue per US GAAP (they are pass-through liabilities).”
- **related-only** · `[^revenue-policy]` — shipping_amount — NUMERIC(18,4) — Carrier charge billed to the customer. Excluded from revenue (pass-through liability).
  - [source only partially states this] The source confirms that shipping is excluded from revenue as a pass-through liability, but it does not define the 'shipping_amount' field as a NUMERIC(18,4) data type.
  - evidence quote: “Shipping and tax are excluded from revenue per US GAAP (they are pass-through liabilities).”
- **related-only** · `[^revenue-policy]` — tax_amount — NUMERIC(18,4) — Sales tax collected. Excluded from revenue (pass-through liability).
  - [source only partially states this] The source confirms that tax is excluded from revenue as a pass-through liability, but it does not define the specific data type 'tax_amount — NUMERIC(18,4)'.
  - evidence quote: “Shipping and tax are excluded from revenue per US GAAP (they are pass-through liabilities).”
- **contradicts** · `[^revenue-policy]` — currency — STRING — ISO 4217 currency code. Non-USD orders convert via finance.fx_daily_rates on order_ts date.
  - The policy explicitly mandates that currency conversion must use the delivery date (delivered_ts), directly contradicting the claim that it uses the order date (order_ts).
  - evidence quote: “Multi-currency orders are converted at the daily reference rate published in finance.fx_daily_rates, using the DELIVERY date (delivered_ts), not the order date.”
- **contradicts** · `[^(uncited)]` — channel — STRING — Order origin: web, mobile, marketplace. Marketplace orders (Amazon, eBay) are net-settled and recognized on marketplace payout, not on order_status = 'delivered'.
  - [uncited claim] The provided Revenue Recognition Policy explicitly mandates that revenue is recognized only when an order reaches 'delivered' status plus 30 days, contradicting the claim that marketplace orders are recognized on payout.
  - evidence quote: “Revenue is recognized when a customer order reaches `order_status = 'delivered'` **and** the return window has closed (delivered date + 30 days).”
- **no-evidence** · `[^(uncited)]` — The grain assumption trips up new analysts: SUM(net_amount) GROUP BY order_id is a no-op because there is exactly one row per order. For per-SKU revenue, join order_lines.
  - [uncited claim] The provided evidence defines revenue recognition policies and fiscal year reporting but contains no information regarding database schema, table structures, or the grain of order data.
- **no-evidence** · `[^(uncited)]` — The refunded status is terminal in this table; the refund event itself lives in finance.refunds, keyed on order_id.
  - [uncited claim] The provided evidence outlines revenue recognition policies and fiscal definitions but contains no information regarding the schema, table structures, or the location of refund data.
