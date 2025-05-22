# app/components/step2_ui.py
import pandas as pd
import os
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger("tamu_newsletter")

class Step2UI:
    """UI component for Step 2: Categorizing Events"""
    
    def __init__(self, categorize_callback: Callable):
        """
        Initialize the Step 2 UI
        
        Args:
            categorize_callback: Callback function to execute when categorization is triggered
        """
        self.categorize_callback = categorize_callback
    
    def render(self):
        """Render the Step 2 UI components"""
        # Import streamlit only when needed, not at module level
        import streamlit as st
        
        st.header("Step 2: Categorize Events")
        logger.info("Step 2 header rendered")
        
        # Only show Step 2 if Step 1 is complete and Step 2 is not complete
        if st.session_state.step1_complete and not st.session_state.step2_complete:
            logger.info("Rendering Step 2 UI elements")
            
            # Display OpenAI API key input box (for LLM categorization)
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                api_key = st.text_input("OpenAI API Key (for event categorization)", 
                                      type="password", 
                                      help="Required for LLM-based event categorization. Will be stored as an environment variable for this session only.")
                if api_key:
                    os.environ["OPENAI_API_KEY"] = api_key
                    logger.info("OpenAI API key provided")
            
            # Option to select model
            model_options = ["gpt-3.5-turbo", "gpt-4"]
            selected_model = st.selectbox("Select OpenAI Model", model_options, 
                                        help="GPT-3.5 Turbo is faster and cheaper. GPT-4 may provide better categorization.")
            
            # Store selected model as environment variable
            if selected_model:
                os.environ["OPENAI_MODEL"] = selected_model
                logger.info(f"Selected model: {selected_model}")
            
            # Run categorization button
            if st.button("Run Event Categorization"):
                logger.info("Categorization button clicked")
                
                # Check if API key is provided
                if not os.getenv("OPENAI_API_KEY"):
                    logger.error("OpenAI API key not provided")
                    st.error("OpenAI API key is required for categorization. Please enter it above.")
                else:
                    with st.spinner("Categorizing events... This may take a few minutes."):
                        # Call the categorize callback (debug_mode removed)
                        self.categorize_callback(api_key, selected_model)
        
        # Display categorized events if Step 2 is complete
        self._display_categorized_events_if_complete()
    
    def _display_categorized_events_if_complete(self):
        """Display categorized events if Step 2 is complete"""
        # Import streamlit only when needed
        import streamlit as st
        
        if st.session_state.step1_complete and st.session_state.step2_complete:
            logger.info("Displaying categorized events")
            
            categorized_events = st.session_state.categorized_events
            
            # Display date range
            date_range = categorized_events.get("date_range", {})
            start_date = date_range.get("start_date", "N/A")
            end_date = date_range.get("end_date", "N/A")
            st.write(f"Showing categorized events from {start_date} to {end_date}")
            
            # Show categorized CTE events
            st.subheader("CTE Events Categories")
            cte_categories = categorized_events.get("cte_events", [])
            
            if cte_categories:
                for i, category in enumerate(cte_categories):
                    category_name = category.get("category_name", "Unnamed Category")
                    category_description = category.get("description", "")
                    events = category.get("events", [])
                    
                    with st.expander(f"{category_name} ({len(events)} events)"):
                        st.write(category_description)
                        
                        # Display events in a table
                        events_df = pd.DataFrame([
                            {
                                "Event Name": event.get("event_name", ""),
                                "Date": event.get("event_date", ""),
                                "Time": event.get("event_time", ""),
                                "Location": event.get("event_location", "")
                            }
                            for event in events
                        ])
                        st.dataframe(events_df)
                
                logger.info(f"Displayed {len(cte_categories)} CTE event categories")
            else:
                st.write("No CTE event categories found.")
                logger.info("No CTE categories to display")
            
            # Show categorized ELP events
            st.subheader("ELP Events Categories")
            elp_categories = categorized_events.get("elp_events", [])
            
            if elp_categories:
                for i, category in enumerate(elp_categories):
                    category_name = category.get("category_name", "Unnamed Category")
                    category_description = category.get("description", "")
                    events = category.get("events", [])
                    
                    with st.expander(f"{category_name} ({len(events)} events)"):
                        st.write(category_description)
                        
                        # Display events in a table
                        events_df = pd.DataFrame([
                            {
                                "Event Name": event.get("event_name", ""),
                                "Date": event.get("event_date", ""),
                                "Time": event.get("event_time", ""),
                                "Location": event.get("event_location", "")
                            }
                            for event in events
                        ])
                        st.dataframe(events_df)
                
                logger.info(f"Displayed {len(elp_categories)} ELP event categories")
            else:
                st.write("No ELP event categories found.")
                logger.info("No ELP categories to display")
            
            # Option to restart categorization
            if st.button("Recategorize Events"):
                logger.info("User requested to recategorize events")
                st.session_state.step2_complete = False
                st.rerun()
            
            # Button to proceed to Step 3
            if not st.session_state.step3_complete:
                if st.button("Approve Categories and Generate Newsletter"):
                    logger.info("User approved categories and proceeding to step 3")
                    st.rerun()