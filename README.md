# TAMU Event Newsletter Generator

A Streamlit application that automates the process of creating event newsletters for the Center for Teaching Excellence at Texas A&M University.

## Features

- Scrape events from TAMU calendars
- Automatically categorize events using AI
- Generate formatted HTML newsletters
- Simple and intuitive UI

## Installation

### Prerequisites

- Python 3.8 or higher
- Chrome browser (for web scraping)

### Setup Instructions

1. Clone the repository:

```bash
git clone https://github.com/yourusername/tamu-newsletter-generator.git
cd tamu-newsletter-generator
```

2. Create and activate a virtual environment:

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit application:

```bash
streamlit run app.py
```

2. The application will open in your default web browser at `http://localhost:8501`

3. Follow the three-step process in the application:
   - Step 1: Scrape events from TAMU calendars
   - Step 2: Categorize events using AI (requires OpenAI API key)
   - Step 3: Generate a formatted HTML newsletter

4. Download the resulting HTML newsletter to use in your email campaigns

## API Keys

For event categorization (Step 2), you'll need an OpenAI API key. You can input this directly in the application interface when prompted.

## Directory Structure

```
app/
├── app.py                 # Main Streamlit entry point
├── components/            # UI components
│   ├── __init__.py
│   ├── step1_ui.py        # UI for step 1
│   ├── step2_ui.py        # UI for step 2
│   ├── step3_ui.py        # UI for step 3
│   └── sidebar_ui.py      # Sidebar status display
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── logger.py          # Logging setup
│   ├── process_runner.py  # Subprocess handling
│   └── state_manager.py   # Session state management
└── services/              # Business logic
    ├── __init__.py
    ├── scraper.py         # Event scraping logic
    ├── categorizer.py     # Event categorization logic
    └── newsletter.py      # Newsletter generation logic
```

## Troubleshooting

- **Scraping Issues**: Make sure Chrome is installed and up to date.
- **Categorization Issues**: Verify your OpenAI API key is correct and has sufficient credits.
- **App Crashes**: Check the log file at `app_debug.log` for detailed error information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
