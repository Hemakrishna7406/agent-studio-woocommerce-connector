# From the merchant's problem to a measurable solution

This is the document behind the assignment. The brief is not really "build a
connector" — it is "do you think like a Forward-Deployed Engineer?" A
Forward-Deployed Engineer owns the technical relationship with a merchant
end-to-end: understand the workflow, uncover the real problem behind the
request, build the solution, and **measure its impact**. This page walks that
arc.

## 1. Start with the workflow, not the request

Picture a mid-sized D2C brand. They sell on **WooCommerce** and take payments
through Razorpay. Their operations lead asks, almost as a throwaway:

> "Can your AI agent just tell me what's happening in my store?"

Taken literally, that is a request for a chatbot. Taken seriously, it is a
symptom. Watch what the ops team actually does every morning:

1. Open the WooCommerce admin.
2. Filter orders to `pending` and `failed`, and eyeball the list for orders
   that should have paid but didn't.
3. Export the product list and scan for anything about to go out of stock.
4. When a support ticket arrives, cross-check that customer's order history.

That is **30–60 minutes of manual, repetitive, error-prone work, every day**.

The real problem is not "we need a chatbot." It is: *the merchant's
operational truth is trapped inside a transactional system, and every question
requires a human to go and dig it out.*

## 2. What the connector unlocks

The unit of value is not "an API call". It is a **question the merchant can
now ask in plain language and get an answer to in seconds**:

| Merchant question | Tool | Today | With the connector |
|---|---|---|---|
| "Which payments are stuck or failed today?" | `list_orders(status=...)` | manual filter, ~10 min | seconds |
| "What's about to stock out?" | `list_inventory(...)` | export + scan, ~15 min | seconds |
| "Has this customer bought from us before?" | `get_customer` + `list_orders(customer_id=...)` | 3 screens, ~5 min | seconds |
| "Is SKU-014 in stock, and at what price?" | `search_products(sku=...)` | admin search, ~2 min | seconds |

## 3. Why read-only first — a deliberate product decision

The tempting demo is a *write* agent that "fixes" things. We deliberately did
not build that. An agent that can mutate a merchant's orders is an agent that
can lose a merchant's money. In a customer-facing, revenue-critical system the
first version should be able to **read, and be wrong harmlessly**, while you
earn trust and measure.

Writes come later — behind explicit human approval and an audit trail
(see `docs/limitations.md` §long-term fix). That is the Forward-Deployed
Engineer instinct: ship the smallest thing that delivers real value, with a
blast radius you can defend to the merchant's CFO.

## 4. How we measure impact (the part most submissions skip)

A connector that "works" is table stakes. The job is to move a number. Here is
the instrumentation we would stand up in week one with the merchant:

| Metric | Type | Baseline | Target | How measured |
|---|---|---|---|---|
| Time-to-answer for an ops question | leading | 5–15 min | < 10 s | agent latency p50/p95 |
| Manual ops minutes/day on these tasks | leading | 30–60 | < 10 | merchant ops log / interview |
| Agent task success rate | leading | n/a | > 95% | tool-call success rate |
| Rate-limit / upstream error rate | quality | n/a | < 1% | typed-error counts from the connector |
| Support tickets deflected | lagging | 0 | track | ticket tags |
| Stuck-payment orders caught per week | lagging | unknown | track | `list_orders` result delta |
| Stockouts avoided | lagging | unknown | track | inventory alert → replenishment |

The **leading** metrics tell you whether the connector is *usable*; the
**lagging** ones tell you whether it is *worth paying for*. A Forward-Deployed
Engineer reports both, and does not hide behind "it works on my machine."

## 5. What the merchant gets in week one

- A working agent that answers the four questions above, grounded in their own
  live data.
- A connector they can trust: read-only, least-privilege, bounded, and honest
  about its limits (`docs/capabilities.md`, `docs/limitations.md`).
- A clear path to v2 — webhooks + an index (`docs/webhooks.md`) — so the value
  compounds instead of plateauing.

## 6. What I'd ask the merchant next

The job is not finished when the connector ships; it is finished when the
merchant's number moves. The next discovery questions:

- Which of these questions costs you the most time today?
- What do you do when an order looks "stuck"? What is the ideal outcome?
- If the agent could *act* (retry a payment, reorder stock), what guardrails
  would you need before you'd let it?
- What would make you turn this off?

Those answers decide v2 far more than any API detail does.
