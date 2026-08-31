# Citation-integrity demo — catching planted errors

This bundle demonstrates `okf_adapter.py`, the mode described in the main README as
["Against its own citations."](../../README.md#3-on-a-whole-knowledge-base) It doesn't
search the web — it checks whether a document's claims actually match what the sources
*it cites* say, which is the right check for internal material the web has no opinion on:
policies, metric definitions, schema docs.

## The setup

`bundle/` is a small, self-contained OKF knowledge base for a fictional retailer
("Acme Retail"): a BigQuery table schema, two finance policies, two metric definitions,
and the SQL that computes them. Four errors were deliberately planted into an otherwise
consistent, correct bundle, to see whether the adapter would catch them:

| # | What was planted | Where |
|---|---|---|
| P1 | `net_amount` redefined as `gross_amount + tax_amount` — the policy says `gross_amount - discount_amount`, and says tax is explicitly excluded | `bundle/tables/orders.md` |
| P2 | A fabricated exemption ("orders under $1 are booked to promotional expense") cited to the revenue policy, which says no such thing | `bundle/metrics/revenue.md` |
| P3 | A true statement (`discount_amount`'s definition) re-cited to the *wrong* source — right claim, wrong citation | `bundle/tables/orders.md` |
| P4 | The currency-conversion policy itself edited to use the delivery date instead of the order date, silently breaking a previously-correct claim elsewhere in the bundle | `bundle/policies/revenue-recognition.md` |

One concept, `metrics/gross-margin.md`, was left untouched as a control.

## Result

**4 of 4 planted errors caught, control unaffected.** Full run: [`bundle-reports/REPORT.md`](bundle-reports/REPORT.md);
per-concept detail with the exact evidence quote behind each verdict, e.g.
[`tables/orders.md`](bundle-reports/tables__orders.report.md), which is where P1 and P3 show up.

| Planted error | Expected | Verdict |
|---|---|---|
| P1 — net_amount formula | contradicts | **contradicts** |
| P2 — fabricated exemption | contradicts | **contradicts** |
| P3 — right claim, wrong citation | caught, not a clean pass | **related-only** ("source only partially states this") |
| P4 — policy edited underneath a claim | contradicts | **contradicts** |
| Control — gross-margin.md | unaffected | **verified**, no false positives |

## Reproduce it

```bash
python3 okf_adapter.py examples/okf-citation-demo/bundle --dry
```

`--dry` reports without writing. Drop `--dry` and it stamps `bundle/` in place; the
committed `bundle-reports/` here is what that run actually produced.
