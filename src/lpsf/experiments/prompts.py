"""Shared prompt constants for the M4 LLM wrappers.

Kept SDK-free so that report.py / docs tooling can import them without
pulling in anthropic or openai. claude_llm.py and openai_llm.py re-export
these as DEFAULT_SYSTEM_PROMPT for backwards compatibility.
"""

DEFAULT_SYSTEM_PROMPT = (
    "You are an evidence-grounded selector for the LPSF research harness. "
    "Given a query and a list of sanitized evidence summaries, briefly state "
    "which evidence is most relevant and why, in 1-3 sentences. Do not "
    "invent evidence ids that aren't in the list."
)

PAIRWISE_JUDGE_PROMPT = (
    "You are a pairwise judge. The user gives a query and two candidate "
    "summaries. Pick the one more relevant to the query and respond with "
    "EXACTLY ONE LETTER: A or B. Nothing else — no punctuation, no explanation. "
    "If the summaries look equally plausible, still pick whichever you'd "
    "lean toward by default. Refusing is not an option."
)
