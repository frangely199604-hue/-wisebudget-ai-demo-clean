"""
WiseBudget AI - local AI integration (Ollama)

Wraps a locally-running Ollama model to provide:
  - Personalised, natural-language budget analysis
  - A conversational budgeting assistant the user can ask questions

Everything here degrades gracefully: if the `ollama` package isn't installed,
or the Ollama server isn't running, or the chosen model hasn't been pulled,
the app keeps working using the rule-based helpers in helpers.py.

Ollama runs entirely on the user's machine - no API key, no cost, no data
leaves the computer. Install it from https://ollama.com and pull a model
(for example: `ollama pull llama3.2`).
"""

import helpers

# The Ollama client is optional. If it isn't installed the app still runs
# (rule-based mode), and the AI pages explain how to enable local AI.
try:
    import ollama
    OLLAMA_INSTALLED = True
except ImportError:
    ollama = None
    OLLAMA_INSTALLED = False


# Where the local Ollama server listens, and a sensible default model.
# llama3.2 (~2 GB) is small and fast enough for most laptops; the user can
# pick a bigger model (e.g. llama3.1, mistral, qwen2.5) in the sidebar.
DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"

SYSTEM_PROMPT = """You are WiseBudget AI, a friendly budgeting and financial-education assistant for users in the UK.

Your job:
- Help people understand their income, spending, savings rate and savings goals.
- Explain budgeting concepts in plain, encouraging language.
- Give concrete, practical, actionable budgeting suggestions based on the user's actual numbers.
- Teach general investing and money concepts (risk, diversification, compound growth, emergency funds) at an educational level.

Strict boundaries:
- This is financial EDUCATION, not personal financial advice.
- Never tell the user to buy, sell, or invest in any specific stock, fund, crypto, or product.
- Never promise returns or give tax/legal advice. Suggest a regulated financial adviser for personal-advice questions.
- Always work from the numbers you are given. Do not invent figures.

Finding savings and building action plans:
- Help the user spot possible savings from their bills, subscriptions, transport, food, shopping and other recurring spending.
- Turn a detected opportunity into a clear, practical action plan with concrete, ordered steps the user can act on.
- You may suggest comparison, negotiation, cancellation, downgrade or usage-review actions where the spending suggests a possible saving.
- Never claim a specific provider or product is definitely cheaper, and never tell the user to "switch to <provider>". Do not invent live prices, tariffs, deals or APRs - if live data isn't available, tell the user to compare on official comparison sites or provider websites.
- Do not give financial, legal, tax, investment or regulated debt advice. Treat debt only as general education.
- Always make clear that any saving figures are estimates, not guarantees.

Style:
- Use the pound symbol £ for money amounts (do not write "GBP") and UK context.
- Be warm, concise and non-judgemental. Lead with the most useful point.
- Use short paragraphs and bullet points. Bold the key numbers.
- When you reference a figure, use the one from the user's data."""


# ============================================================
# Client + status
# ============================================================

def get_client(host=None):
    """Return an Ollama client, or None if the package isn't installed."""
    if not OLLAMA_INSTALLED:
        return None
    try:
        return ollama.Client(host=host or DEFAULT_HOST)
    except Exception:
        return None


def _list_model_names(client):
    """Best-effort list of pulled model names, robust across ollama versions."""
    names = []
    try:
        response = client.list()
        models = getattr(response, "models", None)
        if models is None and isinstance(response, dict):
            models = response.get("models", [])
        for model in models or []:
            name = getattr(model, "model", None) or getattr(model, "name", None)
            if name is None and isinstance(model, dict):
                name = model.get("model") or model.get("name")
            if name:
                names.append(name)
    except Exception:
        return None  # couldn't reach the server / parse the list
    return names


def check_status(host=None, model=None):
    """
    Describe whether local AI is ready.
    Returns (is_ready, message) so the UI can show a clear status and the
    exact command to fix any problem.
    """
    model = model or DEFAULT_MODEL

    if not OLLAMA_INSTALLED:
        return (
            False,
            "The `ollama` Python package isn't installed. Run `pip install ollama`.",
        )

    client = get_client(host)
    if client is None:
        return (False, "Couldn't create an Ollama client.")

    names = _list_model_names(client)
    if names is None:
        return (
            False,
            f"Can't reach Ollama at {host or DEFAULT_HOST}. Install it from ollama.com and make sure it's running.",
        )

    base = model.split(":")[0]
    if names and not any(n == model or n.split(":")[0] == base for n in names):
        return (False, f"Model '{model}' isn't downloaded yet. In a terminal run: ollama pull {model}")

    return (True, f"Ollama connected ({model}).")


def _chunk_text(chunk):
    """Pull the incremental text out of an Ollama stream chunk (object or dict)."""
    message = getattr(chunk, "message", None)
    if message is not None:
        content = getattr(message, "content", None)
        if content is not None:
            return content
    if isinstance(chunk, dict):
        return chunk.get("message", {}).get("content", "") or ""
    return ""


def _friendly_error(error, model):
    text = str(error).lower()
    if "not found" in text or "no such model" in text or "try pulling" in text:
        return f"\n\n_(The model '{model}' isn't downloaded. Run `ollama pull {model}` in a terminal.)_"
    if "connection" in text or "refused" in text or "max retries" in text:
        return "\n\n_(Can't reach Ollama. Make sure the Ollama app is running.)_"
    return f"\n\n_(Local AI error: {error})_"


# ============================================================
# Context building (provider-agnostic)
# ============================================================

def build_financial_context(summary, expense_category_totals, goals_data, period_label, saving_opportunities=None):
    """
    Turn the user's numbers into a compact text block the model can reason over.
    `summary` is the dict from helpers.compute_summary.
    `saving_opportunities` is the optional list from
    helpers.generate_saving_opportunities; when provided it is appended so the
    AI can talk through possible savings using the same figures the UI shows.
    """
    lines = [f"Period analysed: {period_label}", ""]

    lines.append("Budget summary:")
    lines.append(f"- Total income: GBP {summary['total_income']:,.2f}")
    lines.append(f"- Total spending (incl. money moved to savings): GBP {summary['total_expenses']:,.2f}")
    lines.append(f"- Living expenses (excludes deliberate savings): GBP {summary['living_expenses']:,.2f}")
    lines.append(f"- Money deliberately saved: GBP {summary['deliberate_savings']:,.2f}")
    lines.append(f"- Remaining balance (income minus all spending): GBP {summary['remaining_balance']:,.2f}")
    lines.append(f"- Savings rate: {summary['savings_rate']:.1f}%")
    lines.append("")

    if expense_category_totals is not None and not expense_category_totals.empty:
        lines.append("Spending by category:")
        for category, amount in expense_category_totals.items():
            share = (amount / summary["total_income"] * 100) if summary["total_income"] > 0 else 0
            lines.append(f"- {category}: GBP {amount:,.2f} ({share:.1f}% of income)")
        lines.append("")

    if goals_data is not None and not goals_data.empty:
        lines.append("Savings goals:")
        for _, goal in goals_data.iterrows():
            status = "OVERDUE" if goal.get("is_overdue") else "on track"
            lines.append(
                f"- {goal['goal_name']}: saved GBP {goal['current_amount']:,.2f} of "
                f"GBP {goal['target_amount']:,.2f} ({goal['progress_percentage']:.0f}% complete, "
                f"deadline {goal['deadline']}, {status})"
            )
        lines.append("")

    if saving_opportunities:
        lines.append("Saving opportunities detected (estimates only, not guarantees):")
        for opp in saving_opportunities:
            lines.append(
                f"- {opp['title']}: current GBP {opp['current_amount']:,.0f}, "
                f"estimated yearly saving GBP {opp['estimated_yearly_saving_low']:,.0f}-"
                f"{opp['estimated_yearly_saving_high']:,.0f}, priority {opp['priority']}"
            )
        lines.append("")

    return "\n".join(lines).strip()


# ============================================================
# Streaming generators (for st.write_stream)
# ============================================================

def stream_insights(client, model, context):
    """
    Stream a personalised budget analysis from the local model.
    Yields text chunks; on error yields a short message and stops (the caller
    can fall back to rule-based insights).
    """
    model = model or DEFAULT_MODEL
    user_prompt = (
        "Here is my budget data:\n\n"
        f"{context}\n\n"
        "Please give me a short, personalised analysis. Cover: how my budget looks overall, "
        "my biggest opportunity to improve, my savings rate, and 2-3 concrete next steps. "
        "Keep it under about 250 words."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        for chunk in client.chat(model=model, messages=messages, stream=True):
            yield _chunk_text(chunk)
    except Exception as error:
        yield _friendly_error(error, model)


def stream_chat(client, model, context, history):
    """
    Stream a reply in the chat assistant.
    `history` is a list of {"role": "user"|"assistant", "content": str}.
    The latest budget context is attached to the system prompt so the
    assistant always answers using up-to-date numbers.
    """
    model = model or DEFAULT_MODEL
    system = (
        SYSTEM_PROMPT
        + "\n\nThe user's current budget data:\n\n"
        + context
        + "\n\nUse these figures when the user asks about their situation."
    )

    messages = [{"role": "system", "content": system}] + list(history)

    try:
        for chunk in client.chat(model=model, messages=messages, stream=True):
            yield _chunk_text(chunk)
    except Exception as error:
        yield _friendly_error(error, model).strip("_ \n")


def stream_saving_opportunity_advice(
    client, model, opportunity, budget_summary=None, period_label="selected period"
):
    """
    Stream a short, personalised explanation and action plan for ONE saving
    opportunity (a dict from helpers.generate_saving_opportunities).

    The rule-based engine has already detected the opportunity and estimated the
    saving range; the AI only re-explains it in a more human, practical way. It
    must not invent prices/providers/APRs or give regulated advice - the system
    prompt enforces that, and the prompt below repeats the key rules.
    """
    model = model or DEFAULT_MODEL
    opp = opportunity or {}

    # Debt is an interest reduction, not a simple bill saving (helpers marks it).
    is_debt = opp.get("saving_kind") == "interest"
    saving_word = "interest reduction" if is_debt else "saving"

    # Pre-format the figures with the £ symbol so the AI echoes £, not "GBP".
    current_amount = opp.get("current_amount", 0)
    monthly_range = (
        f"£{opp.get('estimated_monthly_saving_low', 0):,.2f} to "
        f"£{opp.get('estimated_monthly_saving_high', 0):,.2f}"
    )
    yearly_range = (
        f"£{opp.get('estimated_yearly_saving_low', 0):,.2f} to "
        f"£{opp.get('estimated_yearly_saving_high', 0):,.2f}"
    )

    # Compact, factual block. The model must reason ONLY from these figures.
    lines = [
        f"Detected saving opportunity for the {period_label}:",
        f"- Title: {opp.get('title')}",
        f"- Category: {opp.get('category')}",
        f"- Detected from: {opp.get('detected_from')}",
        f"- Current amount: £{current_amount:,.2f}",
        f"- Estimated monthly {saving_word} range: {monthly_range}",
        f"- Estimated yearly {saving_word} range: {yearly_range}",
        f"- Priority: {opp.get('priority')}",
        f"- Why it matters: {opp.get('why_it_matters')}",
    ]
    if opp.get("action_steps"):
        lines.append("- Existing recommended actions:")
        for step in opp["action_steps"]:
            lines.append(f"  * {step}")
    if opp.get("disclaimer"):
        lines.append(f"- Disclaimer: {opp['disclaimer']}")

    if budget_summary:
        lines.append("")
        lines.append("User's budget context:")
        lines.append(f"- Total income: £{budget_summary.get('total_income', 0):,.2f}")
        lines.append(f"- Total expenses: £{budget_summary.get('total_expenses', 0):,.2f}")
        lines.append(f"- Remaining balance: £{budget_summary.get('remaining_balance', 0):,.2f}")
        lines.append(f"- Savings rate: {budget_summary.get('savings_rate', 0):.1f}%")

    context = "\n".join(lines)

    title = opp.get("title", "Saving opportunity")
    user_prompt = (
        f"{context}\n\n"
        "Write a short, specific and practical saving plan for THIS one opportunity, using the "
        "exact figures above. Follow this structure with these exact headings:\n\n"
        f"{title}\n\n"
        "What this means:\n"
        f"One short paragraph explaining the issue, using the current amount (£{current_amount:,.2f}).\n\n"
        "Estimated impact:\n"
        f"State the estimated monthly {saving_word} range ({monthly_range}) and the yearly "
        f"{saving_word} range ({yearly_range}), and clearly say this is an estimate, not guaranteed.\n\n"
        "Action plan:\n"
        "Give 3 to 5 specific actions tailored to this category, as a short list. Make them "
        "practical and measurable where possible - for example a weekly cap based on the amount, "
        "reducing top-up shops, comparing own-brand vs branded items, planning before shopping, or "
        "limiting deliveries. Build on the existing recommended actions above.\n\n"
        "Final note:\n"
        "One short caution, for example: \"Do not cut essential spending blindly; compare options first.\"\n\n"
        "Rules: use the £ symbol for every amount (never write 'GBP'). Do not name a provider as "
        "definitely cheaper, do not say 'switch to <provider>', and do not invent live prices, "
        "tariffs, deals or APRs. Use words like check, compare, review, consider and look into. "
        "Keep it under about 200 words."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        for chunk in client.chat(model=model, messages=messages, stream=True):
            yield _chunk_text(chunk)
    except Exception as error:
        yield _friendly_error(error, model)
