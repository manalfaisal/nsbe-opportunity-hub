"""
NSBE Opportunity Hub
A centralized, searchable hub for internships, scholarships, fellowships,
conferences, research programs, and professional development opportunities.

Built for the University of San Francisco chapter of the National Society
of Black Engineers (USF NSBE) as an MVP technical leadership project.
"""

import json
import os
from datetime import datetime

import gradio as gr
import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "opportunities.json")

OPPORTUNITY_TYPES = [
    "Internship",
    "Scholarship",
    "Fellowship",
    "Conference",
    "Research",
    "Professional Development",
]

CLASS_YEARS = ["Freshman", "Sophomore", "Junior", "Senior", "Graduate", "All Students"]

LOCATION_TYPES = ["Remote", "In Person", "Hybrid"]

FIELDS = [
    "Software Engineering",
    "Artificial Intelligence",
    "Data Science",
    "Cybersecurity",
    "Product",
    "Research",
    "General STEM",
    "Aerospace Engineering",
    "Biomedical Engineering",
    "Chemical Engineering",
    "Civil Engineering",
    "Computer Engineering",
    "Electrical Engineering",
    "Environmental Engineering",
    "General Engineering",
    "Industrial Engineering",
    "Materials Engineering",
    "Mechanical Engineering",
]

SORT_OPTIONS = [
    "Deadline: Soonest First",
    "Deadline: Latest First",
    "Organization Name (A-Z)",
    "Opportunity Title (A-Z)",
]

ANY_OPTION = "Any"


# ---------------------------------------------------------------------------
# Data loading and helpers
# ---------------------------------------------------------------------------

def load_opportunities(path=DATA_PATH):
    """Load opportunities from a JSON file. Returns an empty list and prints
    a warning instead of crashing if the file is missing or malformed."""
    if not os.path.exists(path):
        print(f"Warning: data file not found at {path}. Starting with no opportunities.")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: could not read opportunities file ({e}). Starting with no opportunities.")
        return []

    if not isinstance(raw, list):
        print("Warning: opportunities.json is not a list. Starting with no opportunities.")
        return []

    cleaned = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        cleaned.append({
            "id": item.get("id", ""),
            "title": str(item.get("title", "Untitled Opportunity")),
            "organization": str(item.get("organization", "Unknown Organization")),
            "type": str(item.get("type", "")),
            "description": str(item.get("description", "")),
            "deadline": str(item.get("deadline", "") or ""),
            "location": str(item.get("location", "")),
            "location_type": str(item.get("location_type", "")),
            "class_years": item.get("class_years", []) if isinstance(item.get("class_years", []), list) else [],
            "fields": item.get("fields", []) if isinstance(item.get("fields", []), list) else [],
            "tags": item.get("tags", []) if isinstance(item.get("tags", []), list) else [],
            "url": str(item.get("url", "")),
            "is_sample": bool(item.get("is_sample", False)),
        })
    return cleaned


def normalize_text(text):
    """Lowercase and strip text for case-insensitive comparisons."""
    if text is None:
        return ""
    return str(text).strip().lower()


def parse_deadline(deadline_str):
    """Safely parse an ISO date string (YYYY-MM-DD). Returns None if empty
    or invalid, so missing deadlines never crash sorting or display."""
    if not deadline_str:
        return None
    try:
        return datetime.strptime(deadline_str.strip(), "%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def format_deadline(deadline_str):
    """Return a friendly display string for a deadline."""
    parsed = parse_deadline(deadline_str)
    if parsed is None:
        return "Not specified"
    return parsed.strftime("%B %d, %Y")


# ---------------------------------------------------------------------------
# Filtering, searching, and sorting
# ---------------------------------------------------------------------------

def matches_search(opp, query):
    """Check whether an opportunity matches a free-text search query."""
    if not query:
        return True
    q = normalize_text(query)

    searchable_fields = [
        opp.get("title", ""),
        opp.get("organization", ""),
        opp.get("description", ""),
        opp.get("location", ""),
    ]
    searchable_lists = [
        opp.get("tags", []),
        opp.get("class_years", []),
        opp.get("fields", []),
    ]

    for field in searchable_fields:
        if q in normalize_text(field):
            return True

    for lst in searchable_lists:
        for value in lst:
            if q in normalize_text(value):
                return True

    return False


def filter_opportunities(opportunities, query="", opp_type=ANY_OPTION, class_year=ANY_OPTION,
                          location_type=ANY_OPTION, field=ANY_OPTION):
    """Filter opportunities by search text and dropdown filters. All filters
    combine together (AND logic)."""
    results = []

    for opp in opportunities:
        if not matches_search(opp, query):
            continue

        if opp_type and opp_type != ANY_OPTION and opp.get("type", "") != opp_type:
            continue

        if class_year and class_year != ANY_OPTION and class_year not in opp.get("class_years", []):
            continue

        if location_type and location_type != ANY_OPTION and opp.get("location_type", "") != location_type:
            continue

        if field and field != ANY_OPTION and field not in opp.get("fields", []):
            continue

        results.append(opp)

    return results


def sort_opportunities(opportunities, sort_by=SORT_OPTIONS[0]):
    """Sort a list of opportunities. Opportunities with missing deadlines
    are always placed after opportunities with known deadlines when sorting
    by deadline."""
    opps = list(opportunities)

    if sort_by == "Deadline: Soonest First":
        opps.sort(key=lambda o: (parse_deadline(o.get("deadline")) is None,
                                  parse_deadline(o.get("deadline")) or datetime.max))
    elif sort_by == "Deadline: Latest First":
        opps.sort(key=lambda o: (parse_deadline(o.get("deadline")) is None,
                                  -(parse_deadline(o.get("deadline")) or datetime.min).timestamp()
                                  if parse_deadline(o.get("deadline")) else 0))
    elif sort_by == "Organization Name (A-Z)":
        opps.sort(key=lambda o: normalize_text(o.get("organization", "")))
    elif sort_by == "Opportunity Title (A-Z)":
        opps.sort(key=lambda o: normalize_text(o.get("title", "")))

    return opps


def recommend_opportunities(opportunities, class_year, field, location_type):
    """Return opportunities matching a student's selected class year, field
    of interest, and preferred location type. No AI or external API is used
    here; this is straightforward rule-based matching."""
    results = []
    for opp in opportunities:
        if class_year and class_year != ANY_OPTION and class_year not in opp.get("class_years", []):
            continue
        if field and field != ANY_OPTION and field not in opp.get("fields", []):
            continue
        if location_type and location_type != ANY_OPTION and opp.get("location_type", "") != location_type:
            continue
        results.append(opp)

    return sort_opportunities(results, "Deadline: Soonest First")


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

def render_opportunity_cards(opportunities):
    """Render a list of opportunities as polished HTML cards."""
    if not opportunities:
        return """
        <div class="empty-state">
            <h3>No opportunities found</h3>
            <p>Try adjusting your search terms or filters to see more results.</p>
        </div>
        """

    cards = []
    for opp in opportunities:
        title = opp.get("title", "Untitled Opportunity")
        org = opp.get("organization", "Unknown Organization")
        opp_type = opp.get("type", "")
        description = opp.get("description", "")
        deadline_display = format_deadline(opp.get("deadline"))
        location = opp.get("location", "Not specified")
        location_type = opp.get("location_type", "")
        class_years = ", ".join(opp.get("class_years", [])) or "Not specified"
        fields = opp.get("fields", [])
        tags = opp.get("tags", [])
        url = opp.get("url", "") or "#"
        is_sample = opp.get("is_sample", False)

        chip_html = "".join(
            f'<span class="chip">{f}</span>' for f in fields
        ) + "".join(
            f'<span class="chip chip-tag">{t}</span>' for t in tags
        )

        sample_badge = '<span class="sample-badge">Demo Data</span>' if is_sample else ""

        card = f"""
        <div class="opp-card">
            <div class="opp-card-header">
                <span class="opp-type-badge">{opp_type}</span>
                {sample_badge}
            </div>
            <h3 class="opp-title">{title}</h3>
            <p class="opp-org">{org}</p>
            <p class="opp-description">{description}</p>
            <div class="opp-meta">
                <div class="opp-meta-item"><strong>Deadline:</strong> {deadline_display}</div>
                <div class="opp-meta-item"><strong>Location:</strong> {location} ({location_type})</div>
                <div class="opp-meta-item"><strong>Eligible Class Years:</strong> {class_years}</div>
            </div>
            <div class="chip-row">{chip_html}</div>
            <a class="apply-button" href="{url}" target="_blank" rel="noopener noreferrer">View Opportunity / Apply</a>
        </div>
        """
        cards.append(card)

    return f'<div class="card-grid">{"".join(cards)}</div>'


# ---------------------------------------------------------------------------
# Load data once at startup
# ---------------------------------------------------------------------------

ALL_OPPORTUNITIES = load_opportunities()


# ---------------------------------------------------------------------------
# Gradio callback functions
# ---------------------------------------------------------------------------

def handle_search(query, opp_type, class_year, location_type, field, sort_by):
    filtered = filter_opportunities(
        ALL_OPPORTUNITIES,
        query=query,
        opp_type=opp_type,
        class_year=class_year,
        location_type=location_type,
        field=field,
    )
    sorted_results = sort_opportunities(filtered, sort_by)
    count_text = f"**{len(sorted_results)} opportunit{'y' if len(sorted_results) == 1 else 'ies'} found**"
    return count_text, render_opportunity_cards(sorted_results)


def handle_recommendation(class_year, field, location_type):
    recommended = recommend_opportunities(ALL_OPPORTUNITIES, class_year, field, location_type)
    count_text = f"**{len(recommended)} recommended opportunit{'y' if len(recommended) == 1 else 'ies'}** based on your selections"
    return count_text, render_opportunity_cards(recommended)


def reset_filters():
    return "", ANY_OPTION, ANY_OPTION, ANY_OPTION, ANY_OPTION, SORT_OPTIONS[0]


# ---------------------------------------------------------------------------
# Custom styling
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
:root {
    --nsbe-black: #1a1a1a;
    --nsbe-gold: #c9a227;
    --usf-green: #00543c;
    --usf-green-light: #0a6b4f;
    --usf-gold: #fdbb30;
    --nsbe-gray: #6b7280;
    --nsbe-light-gray: #f4f4f5;
}

.gradio-container {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
}

.hero-section {
    background: linear-gradient(135deg, #00543c 0%, #1a1a1a 65%);
    color: #ffffff;
    padding: 40px 32px 32px 32px;
    border-radius: 16px;
    margin-bottom: 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
    border-bottom: 4px solid #fdbb30;
}

.hero-eyebrow {
    display: inline-block;
    background: rgba(253, 187, 48, 0.15);
    border: 1px solid rgba(253, 187, 48, 0.5);
    color: #fdbb30;
    font-size: 0.75em;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 999px;
    margin-bottom: 14px;
}

.hero-section h1 {
    color: #ffffff;
    font-size: 2.5em;
    margin: 4px 0 8px 0;
    letter-spacing: 0.3px;
}

.hero-section h1 .accent {
    color: #fdbb30;
}

.hero-section p {
    color: #e8ede9;
    font-size: 1.08em;
    max-width: 680px;
    margin: 6px auto;
}

.hero-tagline {
    font-style: italic;
    color: #b7cbc0 !important;
    font-size: 0.95em !important;
    margin-top: 14px !important;
}

.section-heading {
    border-left: 5px solid #00543c;
    padding-left: 14px;
    margin: 20px 0 12px 0;
}

.section-heading h2 {
    margin: 0;
    color: #1a1a1a;
}

.section-heading .subtext {
    color: #6b7280;
    font-size: 0.9em;
    margin-top: 2px;
}

.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 18px;
    margin-top: 16px;
}

.opp-card {
    background: #ffffff;
    border: 1px solid #e5e5e5;
    border-top: 3px solid #fdbb30;
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    display: flex;
    flex-direction: column;
    transition: box-shadow 0.15s ease, transform 0.15s ease;
}

.opp-card:hover {
    box-shadow: 0 6px 16px rgba(0,84,60,0.12);
    transform: translateY(-2px);
}

.opp-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.opp-type-badge {
    background: #00543c;
    color: #ffffff;
    font-weight: 600;
    font-size: 0.78em;
    padding: 4px 10px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}

.sample-badge {
    background: #f4f4f5;
    color: #6b7280;
    font-size: 0.72em;
    padding: 3px 8px;
    border-radius: 999px;
    border: 1px solid #d4d4d8;
}

.opp-title {
    margin: 4px 0 2px 0;
    color: #1a1a1a;
    font-size: 1.2em;
}

.opp-org {
    color: #6b7280;
    font-weight: 600;
    margin: 0 0 10px 0;
    font-size: 0.95em;
}

.opp-description {
    color: #374151;
    font-size: 0.92em;
    line-height: 1.5;
    margin-bottom: 12px;
    flex-grow: 1;
}

.opp-meta {
    font-size: 0.85em;
    color: #374151;
    margin-bottom: 12px;
}

.opp-meta-item {
    margin-bottom: 4px;
}

.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 14px;
}

.chip {
    background: #f4f4f5;
    color: #1a1a1a;
    font-size: 0.75em;
    padding: 3px 9px;
    border-radius: 999px;
    border: 1px solid #d4d4d8;
}

.chip-tag {
    background: #eaf3ef;
    border-color: #b9d8ca;
    color: #00543c;
}

.apply-button {
    display: inline-block;
    text-align: center;
    background: #1a1a1a;
    color: #ffffff !important;
    font-weight: 600;
    padding: 10px 16px;
    border-radius: 8px;
    text-decoration: none;
    margin-top: auto;
    transition: background 0.15s ease;
}

.apply-button:hover {
    background: #fdbb30;
    color: #1a1a1a !important;
}

.builder-note {
    background: linear-gradient(135deg, #f4faf7 0%, #fdf9ef 100%);
    border: 1px solid #d9ece2;
    border-left: 4px solid #00543c;
    border-radius: 12px;
    padding: 18px 22px;
    margin-top: 16px;
    color: #1a1a1a;
}

.builder-note strong {
    color: #00543c;
}

.empty-state {
    text-align: center;
    padding: 48px 20px;
    color: #6b7280;
}

.disclaimer-box {
    background: #fdf6e3;
    border: 1px solid #ecdca8;
    border-radius: 12px;
    padding: 18px 20px;
    color: #4a3c00;
    margin-top: 12px;
}
"""


# ---------------------------------------------------------------------------
# Build the Gradio app
# ---------------------------------------------------------------------------

with gr.Blocks(css=CUSTOM_CSS, title="NSBE Opportunity Hub", theme=gr.themes.Soft(primary_hue="yellow")) as demo:

    gr.HTML("""
    <div class="hero-section">
        <span class="hero-eyebrow">USF &middot; NSBE</span>
        <h1>NSBE <span class="accent">Opportunity Hub</span></h1>
        <p>One place to find internships, scholarships, fellowships, conferences, research
        programs, and professional development &mdash; instead of five different apps.</p>
        <p class="hero-tagline">Built by a USF NSBE member, for USF NSBE members.</p>
    </div>
    """)

    with gr.Tabs():

        # --- Search & Browse Tab -------------------------------------------------
        with gr.Tab("Browse Opportunities"):
            gr.HTML("""
            <div class="section-heading">
                <h2>Search &amp; Filter</h2>
                <p class="subtext">Type a keyword, stack a few filters, or both &mdash; it all works together.</p>
            </div>
            """)

            with gr.Row():
                search_box = gr.Textbox(
                    label="Search",
                    placeholder="Try: AI, software engineering, scholarship, freshman, remote, research, cybersecurity...",
                    scale=3,
                )
                sort_dropdown = gr.Dropdown(
                    choices=SORT_OPTIONS, value=SORT_OPTIONS[0], label="Sort By", scale=1
                )

            with gr.Row():
                type_dropdown = gr.Dropdown(
                    choices=[ANY_OPTION] + OPPORTUNITY_TYPES, value=ANY_OPTION, label="Opportunity Type"
                )
                class_year_dropdown = gr.Dropdown(
                    choices=[ANY_OPTION] + CLASS_YEARS, value=ANY_OPTION, label="Class Year"
                )
                location_type_dropdown = gr.Dropdown(
                    choices=[ANY_OPTION] + LOCATION_TYPES, value=ANY_OPTION, label="Location Type"
                )
                field_dropdown = gr.Dropdown(
                    choices=[ANY_OPTION] + FIELDS, value=ANY_OPTION, label="Field / Interest"
                )

            with gr.Row():
                search_button = gr.Button("Search", variant="primary")
                reset_button = gr.Button("Reset Filters")

            result_count = gr.Markdown()
            results_html = gr.HTML()

            search_inputs = [search_box, type_dropdown, class_year_dropdown, location_type_dropdown, field_dropdown, sort_dropdown]
            search_outputs = [result_count, results_html]

            search_button.click(fn=handle_search, inputs=search_inputs, outputs=search_outputs)
            search_box.submit(fn=handle_search, inputs=search_inputs, outputs=search_outputs)
            type_dropdown.change(fn=handle_search, inputs=search_inputs, outputs=search_outputs)
            class_year_dropdown.change(fn=handle_search, inputs=search_inputs, outputs=search_outputs)
            location_type_dropdown.change(fn=handle_search, inputs=search_inputs, outputs=search_outputs)
            field_dropdown.change(fn=handle_search, inputs=search_inputs, outputs=search_outputs)
            sort_dropdown.change(fn=handle_search, inputs=search_inputs, outputs=search_outputs)

            reset_button.click(
                fn=reset_filters,
                inputs=[],
                outputs=[search_box, type_dropdown, class_year_dropdown, location_type_dropdown, field_dropdown, sort_dropdown],
            ).then(fn=handle_search, inputs=search_inputs, outputs=search_outputs)

            demo.load(fn=handle_search, inputs=search_inputs, outputs=search_outputs)

        # --- Recommendations Tab --------------------------------------------------
        with gr.Tab("Find Opportunities for Me"):
            gr.HTML("""
            <div class="section-heading">
                <h2>Find Opportunities for Me</h2>
                <p class="subtext">Three quick picks, and we'll narrow the list down for you.</p>
            </div>
            <p>Set your class year, main area of interest, and preferred location type below.
            This is straightforward rule-based matching against your picks &mdash; no AI, no
            external data, nothing mysterious happening behind the scenes.</p>
            """)

            with gr.Row():
                rec_class_year = gr.Dropdown(choices=[ANY_OPTION] + CLASS_YEARS, value=ANY_OPTION, label="Your Class Year")
                rec_field = gr.Dropdown(choices=[ANY_OPTION] + FIELDS, value=ANY_OPTION, label="Your Main Area of Interest")
                rec_location_type = gr.Dropdown(choices=[ANY_OPTION] + LOCATION_TYPES, value=ANY_OPTION, label="Preferred Location Type")

            rec_button = gr.Button("Find Opportunities for Me", variant="primary")

            rec_count = gr.Markdown()
            rec_html = gr.HTML()

            rec_inputs = [rec_class_year, rec_field, rec_location_type]
            rec_outputs = [rec_count, rec_html]

            rec_button.click(fn=handle_recommendation, inputs=rec_inputs, outputs=rec_outputs)
            rec_class_year.change(fn=handle_recommendation, inputs=rec_inputs, outputs=rec_outputs)
            rec_field.change(fn=handle_recommendation, inputs=rec_inputs, outputs=rec_outputs)
            rec_location_type.change(fn=handle_recommendation, inputs=rec_inputs, outputs=rec_outputs)

        # --- About Tab --------------------------------------------------------
        with gr.Tab("About"):
            gr.HTML("""
            <div class="builder-note">
                <strong>Why I built this &mdash; Manal Faisal</strong>
                <p style="margin: 8px 0 0 0;">
                As a USF NSBE member, I kept missing opportunities because they lived in five
                different places &mdash; a LinkedIn post here, a Slack message there, an email I
                forgot to open. This started as a way to fix that for myself, and I figured other
                members were probably running into the same thing. It's still an early version,
                so if you spot something missing or broken, let a chapter officer know.
                </p>
            </div>
            """)

            gr.HTML("""
            <div class="section-heading"><h2>About This Project</h2></div>
            <p><strong>The Problem:</strong> NSBE members often miss out on internships, scholarships,
            fellowships, conferences, research programs, and professional development opportunities
            because relevant information is scattered across LinkedIn, Handshake, Slack, email, and
            individual company websites. There is no single place to find everything at once.</p>

            <p><strong>Who This Is For:</strong> This hub is built for University of San Francisco
            NSBE members who want a faster, simpler way to discover opportunities relevant to their
            class year, interests, and location preferences.</p>

            <p><strong>Why Centralized Access Matters:</strong> When opportunity information is
            scattered, students lose time, miss deadlines, and may never hear about programs they
            would have qualified for. A centralized, searchable hub reduces that friction and helps
            make opportunity information more equitable and accessible within the chapter.</p>

            <p><strong>Project Status:</strong> This is a Minimum Viable Product (MVP) built as a
            community-centered technical leadership project. It demonstrates how a simple, well-organized
            tool can address a real, everyday problem faced by NSBE members.</p>
            """)

            gr.HTML("""
            <div class="disclaimer-box">
                <strong>Disclaimer:</strong>
                <ul>
                    <li>Opportunity information may change at any time.</li>
                    <li>Always verify deadlines and requirements on the official application website
                    before applying.</li>
                    <li>This project is an independent, student-built tool and is <strong>not officially
                    affiliated with the national NSBE organization</strong>.</li>
                    <li>University of San Francisco NSBE is named as the intended community for this
                    project; this does not imply official chapter endorsement unless separately
                    confirmed.</li>
                    <li>Sample opportunities included in this app are clearly labeled demonstration
                    data and should not be treated as confirmed, currently open opportunities.</li>
                </ul>
            </div>
            """)

    gr.HTML("""
    <p style="text-align:center; color:#6b7280; font-size:0.85em; margin-top:24px;">
        NSBE Opportunity Hub &middot; Built by Manal Faisal for USF NSBE &middot;
        Not officially affiliated with the national NSBE organization
    </p>
    """)


if __name__ == "__main__":
    # PORT is set automatically by hosts like Render; locally it falls back to 7860.
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
