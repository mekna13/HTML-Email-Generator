# app.py
"""
TAMU Event Newsletter Generator - Main Streamlit Application
"""

# CRITICAL: Import streamlit and set_page_config FIRST, before anything else
import streamlit as st

# Set page config immediately after importing streamlit
st.set_page_config(page_title="TAMU Event Newsletter Generator", layout="wide")

# Standard library imports
import datetime
import os
import sys
import logging
from pathlib import Path
from typing import Callable

# Add the current directory to Python path for app module imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Set up logging directly here instead of importing logger module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("tamu_newsletter")

# Import app modules
try:
    from utils.state_manager import StateManager
    from services.scraper import EventScraper
    from services.categorizer import EventCategorizer
    from services.newsletter import NewsletterGenerator
    from components.step1_ui import Step1UI
    from components.step2_ui import Step2UI
    from components.step3_ui import Step3UI
    from components.sidebar_ui import SidebarUI
    logger.info("All modules imported successfully")
except ImportError as e:
    logger.error(f"Import error: {e}")
    st.error(f"Failed to import required modules: {e}")
    st.stop()

# Set up logging
logger.info("Starting TAMU Event Newsletter Generator App")

# Initialize session state
StateManager.initialize_states()
logger.info("Session state initialized")

# App title and description
st.title("TAMU Event Newsletter Generator")
st.write("This app automates the process of creating event newsletters for the Center for Teaching Excellence.")
logger.info("App UI header rendered")

# Initialize service objects
event_scraper = EventScraper()
event_categorizer = EventCategorizer()
newsletter_generator = NewsletterGenerator()

def scrape_events_callback(start_date, end_date):
    """Callback function for Step 1: Scrape Events"""
    logger.info(f"Scraping events from {start_date} to {end_date}")
    
    try:
        # Call the scraper service
        success, events_data = event_scraper.scrape_events(start_date, end_date)
        
        if success:
            # Store results in session state
            StateManager.set_state("events_data", events_data)
            StateManager.set_state("step1_complete", True)
            
            logger.info("Step 1 completed successfully")
            st.success("Events scraped successfully!")
            st.rerun()
        else:
            # Display error message
            error_msg = events_data.get("error", "Unknown error during scraping")
            logger.error(f"Error in scraping: {error_msg}")
            st.error(error_msg)
    except Exception as e:
        logger.error(f"Exception in scrape_events_callback: {e}")
        st.error(f"An error occurred during scraping: {e}")

def categorize_events_callback(api_key: str, model: str, provider: str = "openwebui"):
    """
    Callback function for Step 2: Categorize Events
    SECURE: API key is passed through but never stored anywhere
    """
    logger.info(f"Categorizing events with model {model}")
    
    try:
        # SECURE: Clear any potential leftover environment variables first
        env_keys_to_clear = ['OPENAI_API_KEY', 'OPENAI_MODEL', 'OPENAI_ORG']
        for key in env_keys_to_clear:
            if key in os.environ:
                del os.environ[key]
                logger.info(f"Cleared environment variable: {key}")
        
        # SECURE: Pass API key directly to service, don't store anywhere
        success, categorized_events = event_categorizer.categorize_events(api_key, model, provider)
        
        # SECURE: Clear API key from memory immediately after use
        api_key = None
        del api_key
        
        if success:
            # Store results in session state
            StateManager.set_state("categorized_events", categorized_events)
            StateManager.set_state("step2_complete", True)
            
            logger.info("Step 2 completed successfully")
            st.success("Events categorized successfully!")
            st.rerun()
        else:
            # Display error message
            error_msg = categorized_events.get("error", "Unknown error during categorization")
            logger.error(f"Error in categorization: {error_msg}")
            st.error(error_msg)
            
    except Exception as e:
        logger.error(f"Exception in categorize_events_callback: {e}")
        
        # Handle specific API-related errors
        error_message = str(e).lower()
        if "invalid api key" in error_message or "authentication" in error_message:
            st.error("❌ Invalid API key. Please check your OpenAI API key and try again.")
        elif "quota" in error_message or "rate limit" in error_message:
            st.error("⚠️ API quota exceeded or rate limit reached. Please try again later.")
        else:
            st.error(f"❌ An error occurred during categorization: {e}")
            
    finally:
        # SECURE: Ensure API key is cleared from memory even if exception occurs
        try:
            api_key = None
            del api_key
        except:
            pass  # Already cleared

def generate_newsletter_callback():
    """Callback function for Step 3: Generate Newsletter"""
    logger.info("Generating newsletter")
    
    try:
        # Call the newsletter generator service
        success, html_content = newsletter_generator.generate_newsletter()
        
        if success:
            # Store results in session state
            StateManager.set_state("html_content", html_content)
            StateManager.set_state("step3_complete", True)
            
            logger.info("Step 3 completed successfully")
            st.success("Newsletter generated successfully!")
            st.rerun()
        else:
            # Display error message
            logger.error(f"Error in newsletter generation: {html_content}")
            st.error(html_content)
    except Exception as e:
        logger.error(f"Exception in generate_newsletter_callback: {e}")
        st.error(f"An error occurred during newsletter generation: {e}")

# Main app execution
def main():
    """Main function to render the app"""
    try:
        # Render UI components
        sidebar_ui = SidebarUI()
        sidebar_ui.render()

        step1_ui = Step1UI(scrape_events_callback)
        step1_ui.render()

        step2_ui = Step2UI(categorize_events_callback)
        step2_ui.render()

        step3_ui = Step3UI(generate_newsletter_callback)
        step3_ui.render()

        logger.info("Streamlit app rendering completed")
    except Exception as e:
        logger.error(f"Error in main app execution: {e}")
        st.error(f"An error occurred: {e}")

# Run the app
if __name__ == "__main__":
    main()