# NSBE Opportunity Hub

A centralized, searchable hub for internships, scholarships, fellowships, conferences, research programs, and professional development opportunities — built for University of San Francisco NSBE members.

## Project Overview

NSBE Opportunity Hub is a lightweight web application built with Python and Gradio. It organizes opportunity listings into a single searchable, filterable interface so students no longer have to piece together information from LinkedIn, Handshake, Slack, email threads, and individual company websites. This is an MVP (Minimum Viable Product) built as a community-centered technical leadership project.

## Problem Statement

NSBE members frequently miss out on relevant opportunities simply because information is scattered across too many platforms. There is no single, reliable place where students can go to see what's currently available, who it's for, and when it's due. This fragmentation costs students time and, in some cases, causes them to miss deadlines for programs they would have otherwise qualified for.

## Target Audience

This project is built for **University of San Francisco NSBE members** — from first-year students exploring their first internship to graduate students looking for research assistantships or fellowships.

## Features

- **Search** across opportunity titles, organizations, descriptions, tags, eligible class years, and locations (case-insensitive)
- **Filters** for opportunity type, class year, location type, and field/interest — all combinable with search
- **Sorting** by deadline (soonest or latest first), organization name, or opportunity title, with missing deadlines always placed last
- **Find Opportunities for Me** — a simple, rule-based recommendation tool that matches opportunities to a student's selected class year, area of interest, and location preference (no AI or external API required)
- **Polished opportunity cards** showing all key details plus a clear "View Opportunity / Apply" link
- **About section** explaining the project's purpose, audience, and technical leadership context
- **Visible disclaimer** about data accuracy and NSBE affiliation

## Technology Used

- **Python** — application logic
- **Gradio** — web interface and UI components
- **Pandas** — included for data handling and future extensibility
- **JSON** — local data storage (`opportunities.json`)
- **Hugging Face Spaces** — hosting and deployment

No database, authentication, user accounts, paid APIs, or web scraping are used. The app requires no API key to run.

## File Structure

```
nsbe-opportunity-hub/
│
├── app.py                 # Main Gradio application
├── opportunities.json     # Sample opportunity data (demonstration data)
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── assets/
    └── .gitkeep            # Placeholder so the folder is tracked in git
```

## Local Setup Instructions

1. Clone or download this project folder.
2. (Recommended) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   python app.py
   ```
5. Open the local URL shown in your terminal (typically `http://127.0.0.1:7860`).

## Hugging Face Spaces Deployment Instructions

1. Create a free account at [huggingface.co](https://huggingface.co) if you don't already have one.
2. Click **New Space**.
3. Choose:
   - **SDK:** Gradio
   - **Space name:** e.g. `nsbe-opportunity-hub`
   - **Visibility:** Public or Private, as preferred
4. Once the Space is created, upload these files directly through the Hugging Face web interface (or push via git):
   - `app.py`
   - `opportunities.json`
   - `requirements.txt`
   - `README.md`
   - `assets/` folder (optional)
5. Hugging Face Spaces will automatically install the packages listed in `requirements.txt` and launch the app using `app.py`.
6. Your app will be live at a URL like `https://huggingface.co/spaces/your-username/nsbe-opportunity-hub`.

No API keys or secrets need to be configured for this project.

## How to Add or Edit Opportunities

All opportunity data lives in `opportunities.json`. To add a new opportunity, add a new object to the JSON array using this structure:

```json
{
  "id": 15,
  "title": "Opportunity Title",
  "organization": "Organization Name",
  "type": "Internship",
  "description": "A short description of the opportunity.",
  "deadline": "2027-05-01",
  "location": "City, State or Remote",
  "location_type": "Remote",
  "class_years": ["Sophomore", "Junior"],
  "fields": ["Software Engineering"],
  "tags": ["internship", "summer"],
  "url": "https://example.com",
  "is_sample": true
}
```

Notes:
- `type` must be one of: Internship, Scholarship, Fellowship, Conference, Research, Professional Development.
- `location_type` must be one of: Remote, In Person, Hybrid.
- `class_years` must use values from: Freshman, Sophomore, Junior, Senior, Graduate, All Students.
- `deadline` must use `YYYY-MM-DD` format, or an empty string `""` if there is no confirmed deadline.
- Set `is_sample` to `false` once an opportunity has been verified as a real, currently available listing.
- Always verify real opportunity details and links before removing the sample label.

After editing the file, restart the app (or refresh the Hugging Face Space) to see the changes.

## Data Disclaimer

- Opportunity information may change at any time.
- Users should always verify deadlines and requirements on the official application website before applying.
- This project is **not officially affiliated with the national NSBE organization**.
- University of San Francisco NSBE is named as the intended community for this project; this does not imply official chapter endorsement unless separately confirmed.
- All opportunities currently included in `opportunities.json` are labeled as **demonstration/sample data** (`is_sample: true`) and should not be treated as confirmed, currently open opportunities.

## Future Improvements

The following features are intentionally **not** built in this MVP, but are natural next steps:

- A real database (e.g., PostgreSQL or SQLite) in place of the local JSON file
- Admin-facing submission forms for chapter leaders to add opportunities
- Deadline reminder notifications
- Saved/bookmarked opportunities for individual users
- Verified, live opportunity feeds pulled from trusted sources
- Personalized AI-powered recommendations
- Usage analytics to understand which opportunities students engage with most

## Technical Leadership Connection

This project was created to address a real, everyday bottleneck experienced by USF NSBE members: relevant opportunities being scattered across many disconnected platforms, making them easy to miss. Rather than proposing a purely theoretical solution, this MVP demonstrates practical technical leadership by identifying a community need, scoping a realistic and achievable solution, and shipping a working, deployable tool — using a simple, sustainable tech stack that a student organization can realistically maintain going forward.
