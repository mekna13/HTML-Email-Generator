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
            
            # SECURE: Always prompt for API key, never store it anywhere
            # Always ask for API key input - never check environment or session
            api_key = st.text_input(
                "OpenAI API Key (required for event categorization)", 
                type="password", 
                help="Your API key will only be used temporarily for categorization and will not be stored.",
                placeholder="sk-..."
            )
            
            # Option to select provider
            provider_options = ["openwebui", "openai"]
            selected_provider = st.selectbox("Select Provider", provider_options,
                                            help="Choose 'openwebui' to use TAMU AI chat resources or 'openai' if you want to use OpenAI's API directly.")
                        
            # Run categorization button - only enabled if API key is provided
            if not api_key or not selected_provider:
                st.info("👆 Please enter API key and select provider above to enable categorization.")
                st.button("Run Event Categorization", disabled=True)
            else:
                if st.button("Run Event Categorization", type="primary"):
                    logger.info("Categorization button clicked")
                    
                    # Validate API key format (basic check)
                    if not api_key.startswith("sk-") or len(api_key) < 20:
                        st.error("❌ Invalid API key format. OpenAI API keys start with 'sk-' and are much longer.")

                    if selected_provider != "openwebui" and selected_provider != "openai":
                        st.error("❌ Invalid provider selected. Please choose either 'openwebui' or 'openai'.")
                    else:
                        with st.spinner("Categorizing events... This may take a few minutes."):
                            # Call the categorize callback with API key
                            # SECURE: Pass API key directly, don't store anywhere
                            self.categorize_callback(api_key, selected_provider)

                            # SECURE: Clear the API key from memory after use
                            api_key = None
                            del api_key
        
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
            
            # Show weekly events
            self._display_weekly_events(categorized_events)
            
            # Option to restart categorization
            if st.button("Recategorize Events"):
                logger.info("User requested to recategorize events")
                st.session_state.step2_complete = False
                st.rerun()
            
            # # Button to proceed to Step 3
            # if not st.session_state.step3_complete:
            #     if st.button("Approve Categories and Generate Newsletter"):
            #         logger.info("User approved categories and proceeding to step 3")
            #         st.rerun()
    
    def _display_weekly_events(self, categorized_events: Dict[str, Any]):
        """Display weekly events section"""
        # Import streamlit only when needed
        import streamlit as st
        
        st.subheader("Weekly Events")
        weekly_events = categorized_events.get("weekly_events", [])
        
        if weekly_events:
            st.info(f"Found {len(weekly_events)} weekly event series. These events occur multiple times per week and are displayed as consolidated entries.")
            
            for weekly_event in weekly_events:
                category_name = weekly_event.get("category_name", "Unnamed Weekly Event")
                description = weekly_event.get("description", "")
                weekly_info = weekly_event.get("weekly_event_info", "")
                event_link = weekly_event.get("event_link", "")
                registration_link = weekly_event.get("event_registration_link", "")
                
                with st.expander(f"📅 {category_name} (Weekly Series)"):
                    # Display description
                    if description:
                        st.write("**Description:**")
                        st.write(description)
                    
                    # Display weekly schedule and facilitator info
                    if weekly_info:
                        st.write("**Schedule & Facilitators:**")
                        st.info(weekly_info)
                    
                    # Display links
                    col1, col2 = st.columns(2)
                    with col1:
                        if event_link:
                            st.markdown(f"🔗 [Event Details]({event_link})")
                    with col2:
                        if registration_link:
                            st.markdown(f"📝 [Register Here]({registration_link})")
                    
                    # Add some spacing
                    st.write("")
            
            logger.info(f"Displayed {len(weekly_events)} weekly event series")
        else:
            st.write("No weekly events found in the specified date range.")
            logger.info("No weekly events to display")
    
    def _create_weekly_events_summary_table(self, weekly_events: list) -> pd.DataFrame:
        """Create a summary table for weekly events"""
        summary_data = []
        
        for weekly_event in weekly_events:
            # Extract schedule information from weekly_event_info
            weekly_info = weekly_event.get("weekly_event_info", "")
            
            # Try to extract days and times (basic parsing)
            import re
            
            # Look for day patterns
            days_match = re.findall(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)s?', weekly_info)
            days = ", ".join(set(days_match)) if days_match else "See details"
            
            # Look for time patterns
            times_match = re.findall(r'(\d{1,2}:\d{2}[ap]m[\s-]*\d{1,2}:\d{2}[ap]m)', weekly_info)
            times = "; ".join(set(times_match)) if times_match else "See details"
            
            summary_data.append({
                "Event Series": weekly_event.get("category_name", ""),
                "Days": days,
                "Times": times,
                "Format": "Virtual" if "Virtual" in weekly_info or "Zoom" in weekly_info else "Mixed/Physical"
            })
        
        return pd.DataFrame(summary_data)
    
    def _display_weekly_events_summary(self, weekly_events: list):
        """Display a summary table of weekly events"""
        # Import streamlit only when needed
        import streamlit as st
        
        if weekly_events:
            st.write("**Weekly Events Summary:**")
            summary_df = self._create_weekly_events_summary_table(weekly_events)
            st.dataframe(summary_df, use_container_width=True)
            
            # Add explanation
            st.caption("📌 Weekly events occur multiple times per week. Click on individual events above for complete schedule details.")