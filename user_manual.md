# Fetcher.io — User Manual

**Ask a question. Get the data. No SQL knowledge needed.**

Fetcher.io lets you query the Derivium bond database using plain English — the same way you'd ask a colleague. Type what you want to know, and the system figures out how to retrieve it.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Asking Your First Question](#2-asking-your-first-question)
3. [Understanding the Results](#3-understanding-the-results)
4. [Sorting and Filtering Results](#4-sorting-and-filtering-results)
5. [How to Ask Better Questions](#5-how-to-ask-better-questions)
6. [Example Questions by Topic](#6-example-questions-by-topic)
7. [Your Data is Always Safe](#7-your-data-is-always-safe)
8. [Tips and Shortcuts](#8-tips-and-shortcuts)

---

## 1. Getting Started

Open your browser and go to the Fetcher.io address your team has shared with you (e.g. `http://localhost:8000`). You will see a two-panel screen:

- **Left panel** — where you type your question and see the generated SQL
- **Right panel** — where your results appear as a table

No login, no setup, no installation required on your end. Just open and ask.

---

## 2. Asking Your First Question

1. Click inside the text box on the left that says *"Ask anything about the database…"*
2. Type your question in plain English
3. Press **Run Query** or hit **Ctrl + Enter** (Windows) / **Cmd + Enter** (Mac)

That's it. Within a few seconds your results will appear on the right.

> **Example:**
> *Show all NABARD bonds maturing in the next 2 years*

Fetcher.io reads your question, understands what you mean, and retrieves the exact data — without you writing a single line of code.

---

## 3. Understanding the Results

Once your query runs, you will see several things on screen:

### The Results Table (right panel)

Your data appears as a clean table with one row per bond/record. Columns are automatically sized and you can scroll horizontally if there are many fields.

The **row count** at the top of the table tells you how many records were returned, for example: *1 247 rows returned*.

### The Generated SQL (left panel)

Below your question, Fetcher.io shows the SQL query it created. You do not need to understand this — it is there for transparency so you always know exactly what was asked of the database. You can copy it using the **copy icon** next to the heading.

### The Validation Badge

Every query that runs successfully shows a green **Validated — read only** badge. This confirms that Fetcher.io checked the query before running it and guaranteed it only reads data — it cannot change, delete, or overwrite anything in the database. Your data is completely safe.

### Timing Information

Below the badge you will see how long the query took:
- **LLM** — time to understand your question and generate SQL
- **Database** — time to fetch the results
- **Total** — end-to-end time

Most queries complete in 2–4 seconds.

---

## 4. Sorting and Filtering Results

Once results are on screen, you can explore them without asking a new question.

### Sorting

Click any **column header** to sort the entire table by that column:
- First click → sorted A → Z (or lowest to highest for numbers)
- Second click → sorted Z → A (or highest to lowest)
- Third click → back to original order

A small arrow (↑ or ↓) appears next to the column name to show which direction it is sorted.

### Filtering

Each column has a small **filter box** directly beneath its header. Start typing to instantly narrow the rows shown:

- Type `NABARD` under the issuer column to show only NABARD rows
- Type `AAA` under the rating column to show only AAA-rated rows
- You can filter multiple columns at the same time — only rows matching all filters will show

The row count updates live: *42 of 1 247 rows* tells you 42 rows matched your filter out of 1 247 total.

Filters do not re-query the database — they work instantly on the data already loaded.

---

## 5. How to Ask Better Questions

Fetcher.io understands natural language well, but a few habits will get you better results every time.

### Be specific about what you want to see

| Less specific | More specific |
|---|---|
| Show me bonds | Show all PSU bonds maturing in 2026 |
| NABARD data | Show all NABARD issuances in the last 6 months |
| Recent trades | Show the last traded yield for all IRFC bonds |

### Mention the issuer, rating, or sector clearly

The system knows common abbreviations and full names equally well:

- *PFC*, *Power Finance Corporation* — both work
- *IRFC*, *Indian Railway Finance Corporation* — both work
- *AAA*, *AA+*, *AA* — use rating symbols exactly as written

### Use natural time expressions

- *"in the last 6 months"*
- *"maturing in the next 2 years"*
- *"issued after January 2024"*
- *"between April 2025 and March 2026"*

The system always uses today's actual date — you never need to type a specific date unless you want a precise range.

### Ask for what you care about

- If you want a count: *"How many PSU bonds are rated AAA?"*
- If you want a ranking: *"Top 10 bonds by issue size"*
- If you want a specific ISIN: *"Show details for ISIN INE134E08KH4"*
- If you want a comparison: *"Show all HFC bonds between 2 and 5 year maturity with their last traded yield"*

### Rephrase if the result looks unexpected

If the answer doesn't seem right, try rewording. For example:
- *"bonds maturing soon"* → try *"bonds maturing in the next 3 months"*
- *"big issuances"* → try *"issuances above 500 crore"*

The system is honest — if it cannot generate a valid query from your question, it will tell you rather than guess.

---

## 6. Example Questions by Topic

### Issuers and Sectors

- Show all NABARD bonds
- List all HFC sector issuances from the last year
- Show all PSU bonds issued by state government entities
- List all NHAI bonds with their issue sizes

### Ratings and Credit Quality

- Show all AAA rated bonds maturing in the next 5 years
- List all bonds with a CRISIL AA+ rating
- How many PSU bonds are rated AAA?
- Show all unrated bonds issued in the last 2 years

### Maturity and Tenure

- Show all bonds maturing in 2026
- List all bonds with a tenure greater than 10 years
- Which bonds are maturing in the next 30 days?
- Show PSU bonds with maturity between 3 and 5 years

### Coupon and Interest

- Show all floating rate bonds
- List all bonds with a coupon above 8%
- Show all tax-free bonds
- List all zero-coupon bonds

### Secondary Market and Trading

- Show the last traded yield for all IRFC bonds
- Which PSU AAA bonds were traded in the last 15 days?
- Show the weighted average yield for all PFC bonds traded this year
- List the top 10 most traded bonds by volume

### Cashflows and Redemptions

- Show the full cashflow schedule for ISIN INE134E08KH4
- Which bonds have upcoming interest payments this month?
- List all amortizing bonds with partial redemptions

### Covenants and Structure

- Show all bonds with a minimum net worth covenant
- List all secured bonds issued by private companies
- Show all AT1 bonds
- List all perpetual bonds with a call option before 2030

---

## 7. Your Data is Always Safe

Fetcher.io is built with a strict read-only guarantee at every level.

Every query generated by the system is automatically checked before it reaches the database. If the generated query attempts to modify, delete, or alter any data in any way, it is **blocked immediately** — it never runs. The green *Validated — read only* badge you see on every successful result is proof this check passed.

This is not just a policy — it is enforced in code. The system physically cannot produce or run a query that writes to the database. You can ask freely, experiment, and explore without any risk of accidentally affecting the data.

Fetcher.io also applies rate limiting on API access, so the database is protected from accidental overload. Your questions are always processed one at a time through a secure, encrypted connection to the database.

---

## 8. Tips and Shortcuts

| Action | How |
|---|---|
| Run a query | Click **Run Query** or press **Ctrl + Enter** |
| Copy the SQL | Click the copy icon next to "Generated SQL" |
| Sort a column | Click the column header |
| Clear a sort | Click the same column header until the arrow disappears |
| Filter a column | Type in the small box below the column header |
| Clear a filter | Delete the text in the filter box |
| Ask a new question | Edit the text box and press **Run Query** — results replace the previous ones |

---

*Fetcher.io — Derivium Bond Database AI*
