# app/components/step1_ui.py
import pandas as pd
import datetime
from datetime import timedelta
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger("tamu_newsletter")

class Step1UI:
    """UI component for Step 1: Scraping Events"""
    
    def __init__(self, scrape_callback: Callable):
        """
        Initialize the Step 1 UI
        
        Args:
            scrape_callback: Callback function to execute when scraping is triggered
        """
        self.scrape_callback = scrape_callback
    
    def render(self):
        """Render the Step 1 UI components"""
        # Import streamlit only when needed, not at module level
        import streamlit as st
        
        st.header("Step 1: Scrape Events")
        logger.info("Step 1 header rendered")
        
        # Only show date inputs if step 1 is not complete
        if not st.session_state.step1_complete:
            logger.info("Rendering Step 1 date inputs")
            # Default date range (today to 2 weeks from now)
            default_start_date = datetime.datetime.now().date()
            default_end_date = default_start_date + timedelta(days=14)
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=default_start_date)
            with col2:
                end_date = st.date_input("End Date", value=default_end_date)
            
            logger.info(f"Date inputs rendered: {start_date} to {end_date}")
            
            if st.button("Scrape Events"):
                logger.info("Scrape Events button clicked")
                with st.spinner("Scraping events... This may take a few minutes."):
                    # Call the scrape callback function (debug_mode removed)
                    self.scrape_callback(start_date, end_date)
        
        # Display events data if step 1 is complete
        self._display_events_if_complete()
    
    def _display_events_if_complete(self):
        """Display events data if Step 1 is complete"""
        # Import streamlit only when needed
        import streamlit as st
        
        if st.session_state.step1_complete and st.session_state.events_data:
            logger.info("Displaying scraped events")
            # Show CTE events
            st.subheader("CTE Events")
            if len(st.session_state.events_data["cte_events"]) > 0:
                cte_df = pd.DataFrame(st.session_state.events_data["cte_events"])
                st.dataframe(cte_df[["event_name", "event_date", "event_time", "event_location", "event_facilitators"]])
                logger.info(f"Displayed {len(st.session_state.events_data['cte_events'])} CTE events")
            else:
                st.write("No CTE events found in the specified date range.")
                logger.info("No CTE events to display")
            
            # Show ELP events
            st.subheader("ELP Events")
            if len(st.session_state.events_data["elp_events"]) > 0:
                elp_df = pd.DataFrame(st.session_state.events_data["elp_events"])
                st.dataframe(elp_df[["event_name", "event_date", "event_time", "event_location", "event_facilitators"]])
                logger.info(f"Displayed {len(st.session_state.events_data['elp_events'])} ELP events")
            else:
                st.write("No ELP events found in the specified date range.")
                logger.info("No ELP events to display")
            
            if not st.session_state.step2_complete:
                # Option to restart step 1 with new dates
                if st.button("Restart with Different Dates"):
                    logger.info("User requested restart with different dates")
                    st.session_state.step1_complete = False
                    st.rerun()
                
                # Button to proceed to step 2
                if st.button("Approve Events and Proceed to Categorization"):
                    logger.info("User approved events and proceeded to step 2")
                    st.session_state.step2_complete = False  # Make sure step 2 starts fresh
                    st.rerun()