"""
NSBE Opportunity Hub
A centralized, searchable hub for internships, scholarships, fellowships,
conferences, research programs, and professional development opportunities.

Built for the University of San Francisco chapter of the National Society
of Black Engineers (USF NSBE) as an MVP technical leadership project.
"""

import html
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
    """Render a list of opportunities as responsive, accessible HTML cards."""
    if not opportunities:
        return """
        <div class="empty-state">
            <div class="empty-icon">⌕</div>
            <h3>No matches yet</h3>
            <p>Try a broader keyword or remove one of the filters.</p>
        </div>
        """

    cards = []
    for opp in opportunities:
        title = html.escape(opp.get("title", "Untitled Opportunity"))
        org = html.escape(opp.get("organization", "Unknown Organization"))
        opp_type = html.escape(opp.get("type", "Opportunity"))
        description = html.escape(opp.get("description", ""))
        deadline_display = html.escape(format_deadline(opp.get("deadline")))
        location = html.escape(opp.get("location", "Not specified"))
        location_type = html.escape(opp.get("location_type", ""))
        class_years = html.escape(", ".join(opp.get("class_years", [])) or "Not specified")
        fields = [html.escape(str(value)) for value in opp.get("fields", [])]
        tags = [html.escape(str(value)) for value in opp.get("tags", [])]
        url = html.escape(opp.get("url", "") or "#", quote=True)
        is_sample = opp.get("is_sample", False)

        chip_html = "".join(f'<span class="chip">{field}</span>' for field in fields[:3])
        if len(fields) > 3:
            chip_html += f'<span class="chip chip-muted">+{len(fields) - 3} more</span>'
        chip_html += "".join(f'<span class="chip chip-tag">{tag}</span>' for tag in tags[:2])

        sample_badge = '<span class="sample-badge">Demo data</span>' if is_sample else '<span class="verified-badge">Official source</span>'

        card = f"""
        <article class="opp-card">
            <div class="opp-card-topline"></div>
            <div class="opp-card-body">
                <div class="opp-card-header">
                    <span class="opp-type-badge">{opp_type}</span>
                    {sample_badge}
                </div>
                <h3 class="opp-title">{title}</h3>
                <p class="opp-org">{org}</p>
                <p class="opp-description">{description}</p>
                <div class="opp-meta-grid">
                    <div class="meta-box"><span class="meta-label">Deadline</span><span>{deadline_display}</span></div>
                    <div class="meta-box"><span class="meta-label">Location</span><span>{location}</span></div>
                    <div class="meta-box"><span class="meta-label">Format</span><span>{location_type or 'Not specified'}</span></div>
                </div>
                <div class="eligibility"><strong>Eligible:</strong> {class_years}</div>
                <div class="chip-row">{chip_html}</div>
            </div>
            <a class="apply-button" href="{url}" target="_blank" rel="noopener noreferrer">
                View opportunity <span aria-hidden="true">↗</span>
            </a>
        </article>
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
    --ink: #151816;
    --muted: #66706a;
    --line: #e4e8e5;
    --canvas: #f6f8f6;
    --surface: #ffffff;
    --green: #00543c;
    --green-2: #087356;
    --green-soft: #eaf4ef;
    --gold: #f2b705;
    --gold-soft: #fff7da;
    --shadow: 0 18px 50px rgba(16, 38, 29, 0.08);
}

.gradio-container {
    max-width: 1280px !important;
    margin: 0 auto !important;
    padding: 24px 28px 40px !important;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    background: var(--canvas) !important;
}

body, .main { background: var(--canvas) !important; }

.hero-section {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(circle at 92% 15%, rgba(242,183,5,.30), transparent 24%),
        radial-gradient(circle at 12% 90%, rgba(255,255,255,.10), transparent 28%),
        linear-gradient(135deg, #003f2d 0%, #00543c 48%, #101713 100%);
    color: white;
    border-radius: 26px;
    padding: 48px 48px 38px;
    box-shadow: var(--shadow);
    margin-bottom: 22px;
}

.hero-inner { max-width: 830px; }
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255,255,255,.10);
    border: 1px solid rgba(255,255,255,.18);
    color: #fff4bd;
    font-size: .78rem;
    font-weight: 800;
    letter-spacing: .12em;
    text-transform: uppercase;
    padding: 7px 12px;
    border-radius: 999px;
}
.hero-section h1 {
    color: white;
    font-size: clamp(2.3rem, 5vw, 4.25rem);
    line-height: .98;
    letter-spacing: -.05em;
    margin: 18px 0 16px;
}
.hero-section .accent { color: #ffd44f; }
.hero-copy {
    color: #e6efe9;
    font-size: 1.08rem;
    line-height: 1.65;
    max-width: 720px;
    margin: 0;
}
.hero-stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin-top: 30px;
    max-width: 720px;
}
.hero-stat {
    background: rgba(255,255,255,.09);
    border: 1px solid rgba(255,255,255,.16);
    border-radius: 16px;
    padding: 14px 16px;
    backdrop-filter: blur(8px);
}
.hero-stat strong { display:block; color:white; font-size:1.35rem; }
.hero-stat span { color:#cfe0d6; font-size:.82rem; }

.tab-nav { border-bottom: 1px solid var(--line) !important; }
button[role="tab"] { font-weight: 700 !important; }

.section-heading {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 20px;
    margin: 24px 0 14px;
}
.section-heading h2 { margin:0; color:var(--ink); font-size:1.55rem; letter-spacing:-.025em; }
.section-heading .subtext { color:var(--muted); margin:4px 0 0; }

.search-shell {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 18px;
    box-shadow: 0 8px 30px rgba(17, 37, 29, .05);
    margin-bottom: 18px;
}

.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(330px, 1fr));
    gap: 20px;
    margin-top: 14px;
}
.opp-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 9px 30px rgba(16,38,29,.055);
    display: flex;
    flex-direction: column;
    min-height: 100%;
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.opp-card:hover {
    transform: translateY(-4px);
    border-color: #c8d8cf;
    box-shadow: 0 18px 42px rgba(16,38,29,.11);
}
.opp-card-topline { height: 5px; background: linear-gradient(90deg, var(--green), var(--gold)); }
.opp-card-body { padding: 20px 20px 14px; flex: 1; }
.opp-card-header { display:flex; justify-content:space-between; gap:10px; align-items:center; }
.opp-type-badge, .verified-badge, .sample-badge {
    display:inline-flex; align-items:center; border-radius:999px; font-size:.72rem; font-weight:800; padding:5px 9px;
}
.opp-type-badge { background:var(--green-soft); color:var(--green); }
.verified-badge { background:#eef7f1; color:#29704e; border:1px solid #d1e7da; }
.sample-badge { background:#f4f4f5; color:#6b7280; border:1px solid #dedee2; }
.opp-title { color:var(--ink); font-size:1.24rem; line-height:1.25; letter-spacing:-.025em; margin:16px 0 4px; }
.opp-org { color:var(--green); font-weight:750; margin:0 0 12px; }
.opp-description { color:#4d5651; line-height:1.58; font-size:.93rem; margin:0 0 16px; }
.opp-meta-grid { display:grid; grid-template-columns:1fr 1fr; gap:9px; margin-bottom:11px; }
.meta-box { background:#f7f9f7; border:1px solid #e9ecea; border-radius:12px; padding:10px 11px; display:flex; flex-direction:column; gap:2px; color:#39423d; font-size:.82rem; }
.meta-label { color:#7a847e; text-transform:uppercase; letter-spacing:.07em; font-size:.64rem; font-weight:800; }
.eligibility { color:#55605a; font-size:.82rem; margin-bottom:12px; }
.chip-row { display:flex; flex-wrap:wrap; gap:6px; }
.chip { background:#f1f4f2; color:#344039; border:1px solid #e0e6e2; font-size:.72rem; padding:4px 8px; border-radius:999px; }
.chip-tag { background:var(--gold-soft); border-color:#f4e3a0; color:#725b00; }
.chip-muted { color:#727a75; }
.apply-button {
    display:flex; align-items:center; justify-content:space-between;
    background:var(--ink); color:white !important; text-decoration:none;
    font-weight:800; padding:14px 20px; transition:background .18s ease;
}
.apply-button:hover { background:var(--green); }

.empty-state {
    background:white; border:1px dashed #cad2cd; border-radius:20px; text-align:center; padding:58px 24px; color:var(--muted);
}
.empty-icon { font-size:2rem; color:var(--green); }
.empty-state h3 { color:var(--ink); margin:8px 0 4px; }
.builder-note, .disclaimer-box {
    border-radius:18px; padding:22px 24px; margin-top:16px;
}
.builder-note { background:linear-gradient(135deg,#eef8f3,#fff9e8); border:1px solid #d8e9df; }
.builder-note strong { color:var(--green); }
.disclaimer-box { background:#fff9e8; border:1px solid #eedf9f; color:#514300; }
.footer-note { text-align:center; color:#7a847e; font-size:.82rem; margin-top:26px; }

button.primary { background:var(--green) !important; border-color:var(--green) !important; }
button.primary:hover { background:var(--green-2) !important; }

@media (max-width: 720px) {
    .gradio-container { padding:14px !important; }
    .hero-section { padding:32px 24px 26px; border-radius:20px; }
    .hero-stats { grid-template-columns:1fr; }
    .card-grid { grid-template-columns:1fr; }
    .opp-meta-grid { grid-template-columns:1fr; }
}
"""


# ---------------------------------------------------------------------------
# Build the Gradio app
# ---------------------------------------------------------------------------

with gr.Blocks(css=CUSTOM_CSS, title="NSBE Opportunity Hub", theme=gr.themes.Soft(primary_hue="yellow")) as demo:

    gr.HTML(f"""
    <section class="hero-section">
        <div class="hero-inner">
            <span class="hero-eyebrow">USF NSBE · Student-built resource</span>
            <h1>Find your next <span class="accent">engineering opportunity.</span></h1>
            <p class="hero-copy">Search internships, scholarships, research programs, conferences, and professional development opportunities without jumping between five different platforms.</p>
            <div class="hero-stats">
                <div class="hero-stat"><strong>{len(ALL_OPPORTUNITIES)}+</strong><span>curated opportunities</span></div>
                <div class="hero-stat"><strong>{len(FIELDS)}</strong><span>engineering fields</span></div>
                <div class="hero-stat"><strong>1 hub</strong><span>built for USF NSBE</span></div>
            </div>
        </div>
    </section>
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

            with gr.Group(elem_classes=["search-shell"]):
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
                    search_button = gr.Button("Search opportunities", variant="primary")
                    reset_button = gr.Button("Clear filters")

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
    <p class="footer-note">
        NSBE Opportunity Hub &middot; Built by Manal Faisal for USF NSBE &middot;
        Not officially affiliated with the national NSBE organization
    </p>
    """)


if __name__ == "__main__":
    # PORT is set automatically by hosts like Render; locally it falls back to 7860.
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
