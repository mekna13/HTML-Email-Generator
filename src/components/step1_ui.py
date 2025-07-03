# app/components/step1_ui.py
import pandas as pd
import datetime
from datetime import timedelta
import logging
from typing import Dict, Any, Callable, Optional  # Added Optional

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
        # Import event editor here to avoid circular imports
        from components.event_editor import EventEditor
        self.event_editor = EventEditor()
    
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
                    # Call the scrape callback function
                    self.scrape_callback(start_date, end_date)
        
        # Display events data if step 1 is complete
        self._display_events_if_complete()
    
    def _display_events_if_complete(self):
        """Display events data if Step 1 is complete"""
        # Import streamlit only when needed
        import streamlit as st
        
        if st.session_state.step1_complete and st.session_state.events_data:
            logger.info("Displaying scraped events with editing capability")
            
            # Show the event editor
            st.session_state.events_data = self.event_editor.render_editor(st.session_state.events_data)
            
            # Navigation buttons
            if not st.session_state.step2_complete:
                st.divider()
                col1, col2 = st.columns(2)
                
                with col1:
                    # Option to restart step 1 with new dates
                    if st.button("🔄 Restart with Different Dates", use_container_width=True):
                        logger.info("User requested restart with different dates")
                        st.session_state.step1_complete = False
                        st.rerun()
                
                # with col2:
                #     # Button to proceed to step 2 - without validation
                #     if st.button("✅ Approve Events and Proceed to Categorization", type="primary", use_container_width=True):
                #         logger.info("User approved events and proceeded to step 2")
                #         st.session_state.step2_complete = False  # Make sure step 2 starts fresh
                #         st.success("✅ Proceeding to categorization...")
                #         st.rerun()