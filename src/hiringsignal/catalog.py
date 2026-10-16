"""Small, versioned employer watchlists; not a global jobs database."""

import re


CATALOG_VERSION = "2026-10-16"
GROUP_NAMES = {
    "none": "Custom employer boards only",
    "ai": "AI companies",
    "developer-tools": "Developer tools",
    "fintech": "Fintech",
    "all": "All curated employers",
}

# Entries are checked against bounded official public feeds before release.
# This is editorial grouping, not an employer endorsement or legal identity.
EMPLOYERS: tuple[dict, ...] = (
    {"name": "ElevenLabs", "board": "ashby:elevenlabs", "groups": ("ai",), "publicBoardUrl": "https://jobs.ashbyhq.com/elevenlabs", "verifiedAt": "2026-10-16"},
    {"name": "Perplexity", "board": "ashby:perplexity", "groups": ("ai",), "publicBoardUrl": "https://jobs.ashbyhq.com/perplexity", "verifiedAt": "2026-10-16"},
    {"name": "Cursor", "board": "ashby:cursor", "groups": ("ai", "developer-tools"), "publicBoardUrl": "https://jobs.ashbyhq.com/cursor", "verifiedAt": "2026-10-16"},
    {"name": "Palantir", "board": "lever:palantir", "groups": ("ai",), "publicBoardUrl": "https://jobs.lever.co/palantir", "verifiedAt": "2026-10-16"},
    {"name": "Figma", "board": "greenhouse:figma", "groups": ("developer-tools",), "publicBoardUrl": "https://job-boards.greenhouse.io/figma", "verifiedAt": "2026-10-16"},
    {"name": "Vercel", "board": "greenhouse:vercel", "groups": ("developer-tools",), "publicBoardUrl": "https://job-boards.greenhouse.io/vercel", "verifiedAt": "2026-10-16"},
    {"name": "Linear", "board": "ashby:linear", "groups": ("developer-tools",), "publicBoardUrl": "https://jobs.ashbyhq.com/linear", "verifiedAt": "2026-10-16"},
    {"name": "Notion", "board": "ashby:notion", "groups": ("developer-tools",), "publicBoardUrl": "https://jobs.ashbyhq.com/notion", "verifiedAt": "2026-10-16"},
    {"name": "Supabase", "board": "ashby:supabase", "groups": ("developer-tools",), "publicBoardUrl": "https://jobs.ashbyhq.com/supabase", "verifiedAt": "2026-10-16"},
    {"name": "Ashby", "board": "ashby:ashby", "groups": ("developer-tools",), "publicBoardUrl": "https://jobs.ashbyhq.com/ashby", "verifiedAt": "2026-10-16"},
    {"name": "PostHog", "board": "ashby:PostHog", "groups": ("developer-tools",), "publicBoardUrl": "https://jobs.ashbyhq.com/PostHog", "verifiedAt": "2026-10-16"},
    {"name": "Stripe", "board": "greenhouse:stripe", "groups": ("fintech",), "publicBoardUrl": "https://job-boards.greenhouse.io/stripe", "verifiedAt": "2026-10-16"},
    {"name": "Coinbase", "board": "greenhouse:coinbase", "groups": ("fintech",), "publicBoardUrl": "https://job-boards.greenhouse.io/coinbase", "verifiedAt": "2026-10-16"},
    {"name": "Plaid", "board": "ashby:plaid", "groups": ("fintech",), "publicBoardUrl": "https://jobs.ashbyhq.com/plaid", "verifiedAt": "2026-10-16"},
)

ROLE_TERMS = {
    "all": (),
    "data-ai": ("data", "machine learning", "ml", "ai", "artificial intelligence", "analytics", "scientist"),
    "engineering": ("engineer", "engineering", "developer", "devops", "sre", "architect"),
    "product-design": ("product manager", "product management", "designer", "design", "ux", "ui"),
    "sales-marketing": ("sales", "marketing", "account executive", "business development", "growth", "demand generation"),
}
ROLE_PATTERNS = {
    key: re.compile(r"(?<!\w)(?:" + "|".join(re.escape(term).replace(r"\ ", r"\s+") for term in terms) + r")(?!\w)", re.IGNORECASE)
    for key, terms in ROLE_TERMS.items() if terms
}


def group_boards(group: str) -> tuple[str, ...]:
    return tuple(item["board"] for item in EMPLOYERS if group == "all" or group in item["groups"])


def employer_for(board_key: str) -> dict | None:
    return next((item for item in EMPLOYERS if item["board"] == board_key), None)


def role_matches(title: str, preset: str) -> bool:
    return preset == "all" or bool(ROLE_PATTERNS[preset].search(title))


def catalog_document() -> dict:
    return {
        "version": CATALOG_VERSION,
        "scope": "curated-employer-watchlists-not-global-search",
        "groups": {key: value for key, value in GROUP_NAMES.items() if key != "none"},
        "employers": [{**item, "groups": list(item["groups"])} for item in EMPLOYERS],
        "rolePresetTitleTerms": {key: list(value) for key, value in ROLE_TERMS.items()},
        "note": "Feed availability was checked on each entry's verifiedAt date; current availability and job counts can change.",
    }


def search_context(config) -> dict:
    return {
        "companyGroup": config.company_group,
        "rolePreset": config.role_preset,
        "roleTitleTerms": list(ROLE_TERMS[config.role_preset]),
        "catalogVersion": CATALOG_VERSION,
        "resolvedBoards": [board.key for board in config.boards],
        "scope": "selected-employer-boards-only",
        "sort": "provider-order-not-newest-first",
    }
