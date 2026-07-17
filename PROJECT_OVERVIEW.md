# WiseBudget AI - Project Overview

*Briefing document for discussing new features and requirements. Reflects the app as of July 2026. Contains no personal data; all figures shown are examples.*

---

## 1. What the project is

**WiseBudget AI** is a local-first, single-user budgeting and financial-education web app for UK users, built with Python and Streamlit. It tracks income, expenses and savings goals in simple CSV files, detects "Smart Saving Opportunities" from spending patterns using a rule engine, and layers optional AI explanations on top using a **locally running Ollama model** (default `llama3.2`). Nothing leaves the user's machine: no accounts, no cloud APIs, no cost.

The owner/developer is a **beginner programmer**, so the codebase deliberately stays simple, readable and well-commented. Any proposed feature should respect that.

---

## 2. Hard constraints (do not violate when proposing features)

These are product rules, not preferences:

1. **Education only, never regulated financial advice.**
   - Never recommend specific investments, stocks, funds, crypto, or providers.
   - Never say "switch to [provider X]" or claim a provider/product is definitely cheaper.
   - Allowed phrasing: "compare providers/tariffs", "review your current plan", "check whether a cheaper SIM-only plan is available", "cancel or rotate unused subscriptions", "use comparison sites or official provider websites".
2. **All savings are labelled as estimates, never guarantees.**
3. **No invented data.** The AI must not make up live prices, tariffs, deals, or APRs. If live data is unavailable it must direct the user to official comparison sites.
4. **Debt is special.** Debt repayment "savings" are presented as *potential interest reduction* (educational), never as a normal bill saving, and are excluded from saving totals because the app has no APR/interest-rate data.
5. **Local and free (current phase):** no paid APIs, no Open Banking, no web scraping, no new heavyweight dependencies.
6. **Stability:** do not change CSV schemas unless absolutely necessary; do not break existing pages.

---

## 3. Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.13 |
| UI framework | Streamlit (single `app.py`, sidebar radio navigation) |
| Data handling | pandas; CSV files on disk (no database) |
| AI | Ollama running locally at `http://localhost:11434`, default model `llama3.2`; the `ollama` Python client |
| Charts | None by design - the user prefers ranked lists and tables over charts (matplotlib was removed from the UI; it is still listed in requirements.txt but unused) |
| Environment | Windows 11, `.venv` virtual environment, run with `streamlit run app.py` |

Dependencies (`requirements.txt`): `streamlit`, `pandas`, `matplotlib` (unused), `ollama`.

**Graceful degradation:** if the `ollama` package is missing, the server is down, or the model is not pulled, every AI feature falls back cleanly - status shows "Rule-based mode" and the rule-based insights still work.

---

## 4. Project structure

```
WiseBudget AI/
  app.py           # all Streamlit UI and pages (~700 lines)
  helpers.py       # pure data/logic: CSV I/O, calculations, categorisation,
                   # rule-based insights, Smart Saving Opportunities (~950 lines)
  ai_helper.py     # local Ollama integration: status checks, context building,
                   # streaming generators (~430 lines)
  requirements.txt
  data/
    income.csv     # columns: date, source, amount
    expenses.csv   # columns: date, description, amount, category
    goals.csv      # columns: goal_name, target_amount, current_amount, deadline
```

Separation rule: `helpers.py` contains no Streamlit code (pure logic, easy to test); `app.py` contains no business logic beyond wiring; `ai_helper.py` is provider-specific AI code.

---

## 5. Data model

CSV files are created automatically with headers if missing. Dates are `YYYY-MM-DD` strings. Money columns are coerced to numeric on load (invalid -> 0).

**Expense categories (fixed list):**
`Food, Transport, Rent, Bills, Subscriptions, Entertainment, Shopping, Savings, Debt Repayment, Health, Education, Other`

Notes:
- `Savings` as an expense category means "money deliberately set aside". The summary maths treats it as kept money, not living cost.
- Example expense row: `2026-06-21, Aldi Shopping, 45.00, Food`

---

## 6. Pages and features

Sidebar navigation: **Dashboard, Add Income, Add Expense, WiseBudget AI Coach, Savings Goals, Investment Learning Hub, Feedback**. The sidebar also has a **Demo Mode toggle** (realistic 3-month example data; real CSVs never touched) and an "AI Settings" expander for the Ollama model/host; a status pill shows "Local AI connected" or "Rule-based mode". A compact header shows a small logo, subtitle and badges (Local-first / Education only / Estimates, not guarantees) plus a slim education-only disclaimer.

### 6.1 Dashboard
- **Period filter**: selectbox with "All time" + each month (YYYY-MM) found in the data. Everything below (except the monthly table) respects it.
- **4 metrics**: Total Income, Total Expenses, Remaining Balance, Savings Rate.
- **Spending by Category**: ranked list, highest first, e.g. `1. Food: £90.00 (43.0%)` (share of total spending). No charts, by explicit user preference.
- **Income vs Expenses by Month**: table (newest first) with Income, Expenses, Net columns.
- **Savings Goals Overview**: progress bar + saved/target per goal, overdue warning.
- **Smart Saving Opportunities** (see section 7): summary box + expandable cards, using the selected period's expenses; headline amount label adapts ("Current monthly amount" for a month, "Current amount for selected period" for All time).
- **Records**: Income and Expenses tables for the period, both sorted highest amount first (display-only sort).
- **Export**: download buttons for the three CSVs.

### 6.2 Add Income / Add Expense
- Simple forms with validation (non-empty source/description, amount > 0).
- Expense category can be chosen manually or via **"Auto Detect"**, a keyword classifier (`auto_categorise_expense`) that maps the description to a category. Matching is whole-word with a trailing-s plural allowance (so "tfl" never matches inside "Netflix", "Sainsburys" still matches "sainsbury"). Food keywords are checked before Shopping so "Aldi Shopping" is Food, not Shopping.
- Each page also has an editable `st.data_editor` grid (add/edit/delete rows) with a save button; edited tables are cleaned (blank rows dropped, money coerced, dates normalised) before saving.

### 6.3 WiseBudget AI Coach (merged: old "AI Budget Insights" + "Ask WiseBudget AI")
One page, in this order:
- Title, subtitle, AI status pill (green connected / amber rule-based).
- **Budget snapshot**: 4 metric cards (all-time totals).
- **Quick checks**: always-available rule-based insights (savings-rate bands, overspend warning, biggest category, category-specific warnings such as food > 25% of income or subscriptions > £50).
- **Smart Saving Opportunities**: same component as the Dashboard, over ALL expenses, month-normalised (label: "Average monthly amount based on selected data" when multi-month).
- **AI budget analysis**: button streams a ~250-word Ollama analysis grounded in the same context; helpful fallback message when AI is unavailable.
- **Chat assistant** (`st.chat_input`/`st.chat_message`): history in session state, Clear chat button, one-click prompt suggestions ("Where am I overspending?", "Which saving opportunity should I review first?", etc.). Context is rebuilt every turn (summary, category totals, goals, month-normalised saving opportunities).

### 6.5 Savings Goals
- Form (name, target, current, deadline) with validation; progress bars, Target/Saved/Remaining metrics, overdue detection; editable grid to fix/delete goals.

### 6.6 Investment Learning Hub
- Static educational content: risk, diversification, compound growth, long-term thinking, emergency funds. Explicitly no recommendations.

---

## 7. Smart Saving Opportunities (the flagship feature)

### 7.1 How detection works (`helpers.generate_saving_opportunities(expenses_data, income_data=None)`)
- A rule table (`SAVING_RULES`) defines 11 opportunity types. Each rule has: keywords, fallback categories, an estimated saving % range, "why it matters" text, and 3-5 recommended actions.
- Per expense: the **longest matching keyword wins** (so "uber eats" -> Food beats "uber" -> Transport). Keyword matching is whole-word with plural allowance.
- **Food-beats-Shopping override**: if the best match is Shopping but any Food keyword is present, it is reclassified Food (fixes "Aldi Shopping"/"Tesco shopping" being called Shopping because the generic word "shopping" is a Shopping keyword).
- If no keyword matches, fall back to the expense's own category.
- Same-type expenses are **combined into one opportunity** with the summed amount (e.g. British Gas £60 + Octopus £40 -> one Energy card at £100).
- Results sorted by priority (High/Medium/Low), then by yearly-high saving, descending.

### 7.2 The 11 rules and estimated saving ranges

| Rule | Trigger examples | Est. saving |
|---|---|---|
| Energy bill | gas, electric, energy, british gas, octopus, edf, eon, ovo, scottish power | 5-15% |
| Mobile/phone | phone, mobile, vodafone, ee, o2, three, giffgaff, sim | 10-30% |
| Broadband/internet | broadband, internet, wifi, virgin media, bt, sky, talktalk | 10-25% |
| Subscriptions | netflix, spotify, disney, prime, youtube premium, icloud + category | 20-50% |
| Food/Groceries | tesco, aldi, lidl, asda, sainsbury, morrisons, groceries, supermarket, food shop(ping), takeaway, uber eats, deliveroo + category Food | 5-20% |
| Transport | uber, bolt, train, tube, tfl, oyster, bus, petrol, fuel, parking, taxi + category | 5-20% |
| Debt repayment (special) | loan, credit card, debt, klarna, paypal credit + category | 5-15% (as *interest reduction*) |
| Shopping | amazon, zara, nike, jd, clothes, shein, asos + category | 10-30% |
| Entertainment | cinema, bar, pub, club, drinks, concert, game + category | 10-30% |
| Gym/Health | gym, fitness, puregym, david lloyd, pharmacy + category Health | 10-40% |
| Education | course, book, university, udemy, coursera, training + category | 10-30% |

**Priority** is based on the best-case yearly saving: High >= £150/yr, Medium >= £50/yr, else Low.

### 7.3 Opportunity dictionary shape (the contract between logic and UI)

```python
{
  "title": "Energy bill detected",
  "category": "Bills",
  "detected_from": "British Gas, Octopus",       # up to 4 descriptions, then "and N more"
  "current_amount": 100.00,
  "saving_percentage_low": 5,
  "saving_percentage_high": 15,
  "estimated_monthly_saving_low": 5.00,
  "estimated_monthly_saving_high": 15.00,
  "estimated_yearly_saving_low": 60.00,
  "estimated_yearly_saving_high": 180.00,
  "priority": "High",                             # High / Medium / Low
  "why_it_matters": "...",
  "action_steps": ["...", "..."],                 # rule-engine recommendations
  "saving_kind": "saving",                        # "interest" for debt (special display)
  "disclaimer": "This is an estimated saving opportunity, not a guaranteed saving."
}
```

### 7.4 Debt special-casing
- Title: "Potential interest saving opportunity"; `saving_kind = "interest"`.
- UI labels its figures "Potential monthly/yearly interest reduction" instead of "Estimated saving".
- Custom disclaimer: "Debt savings depend on interest rate, repayment terms, and whether overpayments are allowed."
- **Excluded from all saving totals** (`summarise_saving_opportunities` skips interest-kind items) because the app has no APR data.

### 7.5 UI (shared `render_saving_opportunities(...)` in app.py)
- **Summary box** above the cards: number of opportunities, total estimated monthly and yearly saving ranges, the note "Estimates exclude debt repayment unless interest-rate data is available.", and "These are estimates only, not guaranteed savings."
- One `st.expander` card per opportunity (top card auto-expanded): detected-from caption, headline amount metric (label adapts to page/period), monthly + yearly range metrics, coloured priority badge, "Why it matters", **"Recommended actions"** (rule engine), per-card disclaimer.
- **"Generate AI saving plan" button** per card (unique key per page/card): only runs on click; streams the plan under an "AI saving plan" heading; result cached in session state so it survives reruns without re-calling the model. If AI is not connected, an info message explains and the rule-based content still stands.

---

## 8. AI integration (`ai_helper.py`)

- `check_status(host, model)` -> (ready, message): detects missing package / unreachable server / model not pulled, each with the exact fix command.
- `build_financial_context(summary, category_totals, goals, period_label, saving_opportunities=None)` -> compact text block of the user's numbers; optionally appends a "Saving opportunities detected" section. Backward-compatible signature.
- `stream_insights(client, model, context)` -> streams the ~250-word budget analysis.
- `stream_chat(client, model, context, history)` -> streams chat replies; context attached to the system prompt.
- `stream_saving_opportunity_advice(client, model, opportunity, budget_summary=None, period_label=...)` -> streams a structured plan for ONE opportunity with exact headings:
  1. *[Opportunity title]*
  2. **What this means:** one paragraph using the current amount
  3. **Estimated impact:** the monthly and yearly £ ranges, explicitly "estimate, not guaranteed"
  4. **Action plan:** 3-5 specific, measurable actions (builds on the rule engine's actions)
  5. **Final note:** a short caution (e.g. "Do not cut essential spending blindly; compare options first.")
- **System prompt** enforces: UK financial-education tone, £ symbol (never "GBP"), work only from given figures, no provider recommendations, no invented prices/tariffs/APRs, no regulated financial/legal/tax/investment/debt advice, savings framed as estimates.
- All streaming functions catch exceptions and yield a friendly one-line fix hint instead of crashing.

---

## 9. Key logic worth knowing (`helpers.py`)

- `compute_summary(income, expenses)` -> dict: total_income, total_expenses, living_expenses (excludes deliberate Savings category), deliberate_savings, remaining_balance, savings_rate (= (income - living_expenses) / income).
- `get_month_options` / `filter_by_month` -> "All time" + YYYY-MM period filtering.
- `auto_categorise_expense(description)` -> category via whole-word keyword map (Food checked before Shopping).
- `category_totals`, `monthly_totals` -> aggregations for the ranked list and the monthly table.
- `prepare_goals_data` -> adds remaining_amount, progress_percentage (clamped 0-100), is_overdue.
- `generate_budget_insights(...)` -> list of (type, message) tuples for the Quick checks (type maps to st.success/info/warning/error).
- `summarise_saving_opportunities(opportunities)` -> totals for the summary box; skips `saving_kind == "interest"`.

---

## 10. UX conventions and owner preferences

- **Lists and tables, not charts.** The owner explicitly removed pie/bar charts in favour of ranked lists ("highest first so the user can see where the majority of money goes").
- £ symbol everywhere in the UI and AI output; British English ("categorise", "analyse").
- Beginner-friendly code: descriptive names, comments explain *why*, no clever abstractions.
- st.expander cards, st.metric for figures, coloured st.info/warning/success for statuses.
- AI is always opt-in per click (never auto-runs), so pages stay fast with a local model.
- Unique Streamlit keys for repeated widgets: `ai_saving_plan_{page}_{index}_{title}`.

---

## 11. Known limitations / technical notes

1. ~~All-time amounts are not normalised per month.~~ **Fixed (July 2026):** `generate_saving_opportunities` takes `months_covered` (from `count_months_covered`), so multi-month data is analysed as an honest monthly average and labelled "Average monthly amount based on selected data".
2. **Keyword detection is heuristic.** Whole-word matching kills the big false positives, but unusual descriptions or new merchants fall back to the category (or are missed if categorised "Other").
3. **No true recurrence detection.** "Recurring" costs are inferred from keywords/categories, not from repeated dates across months.
4. **AI plan cache is session-only** (lost on browser refresh); keyed by page/card/amount.
5. **Single user, no auth, plain CSVs** - fine for local personal use, not multi-user.
6. **Streamlit module caching**: edits to helpers.py/ai_helper.py need a full server restart; app.py edits apply on rerun.
7. matplotlib is still in requirements.txt but unused.
8. Local model quality varies; llama3.2 (~2 GB) occasionally words things awkwardly. Bigger local models (mistral, qwen2.5, llama3.1) can be set in AI Settings.

---

## 12. Open questions / candidate features to discuss

Seed list for the roadmap conversation (none are committed):

1. **Month-normalised estimates**: divide all-time totals by months covered so estimates stay honest on every page.
2. **True recurring-expense detection**: detect the same description appearing across consecutive months; flag price rises (e.g. "Netflix went from £10.99 to £12.00").
3. **Per-category monthly budgets** with progress bars and overspend alerts (schema addition: a budgets.csv).
4. **APR field for debt** (optional user input) so debt cards can show a real modelled interest saving and rejoin the totals.
5. **Reminders**: contract end dates, meter-reading nudges, subscription renewal dates (would need a dates store + some notification mechanism within Streamlit's constraints).
6. **Monthly PDF/HTML report export** (summary, ranked spending, opportunities).
7. **Savings goal integration**: suggest funnelling estimated savings into a chosen goal ("your £54-216/yr estimated food saving could fund 30% of 'Holiday'").
8. **Better data entry**: bank-statement CSV import with column mapping + auto-categorisation pass (still local, no Open Banking).
9. **Test suite** (pytest) for helpers.py - the logic is pure and very testable; plus a lightweight CI.
10. **Optional cloud AI mode** (e.g. Anthropic/OpenAI API) behind an explicit privacy toggle, for users who want stronger models than local Ollama - would need clear data-leaves-device consent. (Currently out of scope by constraint #5.)
11. **Multi-profile support** (e.g. separate data folders per household member).
12. **Accessibility / mobile polish** within Streamlit's limits.

When proposing anything, please check it against the hard constraints in section 2 (especially: education-only wording, estimates-not-guarantees, no provider recommendations, local-first, CSV stability, beginner-maintainable code).

---

## 13. Update log (July 2026 - Phase 1 + design)

- **Demo Mode**: sidebar toggle; `helpers.get_demo_data()` returns 3 months of realistic UK example data; real CSVs never written; Add/edit pages locked while active; amber banner shows "Demo Mode: using example data only".
- **Feedback page**: form saving to `data/feedback.csv` (auto-created; columns: date_time, would_use_app, most_useful_feature, preferred_spending_view, what_was_confusing, feature_to_add, design_rating, usefulness_rating, final_comments).
- **Month-normalised estimates**: see section 11 item 1.
- **Your Top 3 Money Actions**: Dashboard cards for the top non-debt opportunities (title, monthly range, one next step, priority badge). `helpers.top_saving_actions()`.
- **Optional spending views**: Ranked list (default) / Percentages / Bar chart (horizontal, matplotlib) / Pie chart (compact, legend at side) / Table - user-selectable on the Dashboard, inside a bordered card. Charts render as fixed-width images so they stay phone-friendly.
- **Merged AI pages** into **WiseBudget AI Coach** (section 6.3); old "AI Budget Insights" and "Ask WiseBudget AI" pages removed from navigation.
- **Premium design pass**: `inject_custom_css()` - soft gradient background (#F3F6FA -> mint #ECFDF5), white card surfaces (14px radius, subtle shadows), emerald buttons with hover lift, branded sidebar with AI-status pill, compact header with badges, tighter vertical rhythm, columns wrap 2-per-row on phones.
