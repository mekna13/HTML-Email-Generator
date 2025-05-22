# app/components/sidebar_ui.py
import logging

logger = logging.getLogger("tamu_newsletter")

class SidebarUI:
    """UI component for the sidebar status display"""
    
    def render(self):
        """Render the sidebar status components"""
        # Import streamlit only when needed, not at module level
        import streamlit as st
        
        status_container = st.sidebar.container()
        with status_container:
            st.write("## Workflow Status")
            
            # Step 1 status
            if st.session_state.step1_complete:
                st.sidebar.success("Step 1: Events Scraped ✓")
                logger.info("Sidebar status: Step 1 complete")
            else:
                st.sidebar.info("Step 1: Scrape Events")
                logger.info("Sidebar status: Step 1 in progress")
            
            # Step 2 status
            if st.session_state.step2_complete:
                st.sidebar.success("Step 2: Events Categorized ✓")
                logger.info("Sidebar status: Step 2 complete")
            elif st.session_state.step1_complete:
                st.sidebar.info("Step 2: Categorize Events")
                logger.info("Sidebar status: Step 2 in progress")
            else:
                st.sidebar.text("Step 2: Categorize Events")
                logger.info("Sidebar status: Step 2 pending")
            
            # Step 3 status
            if st.session_state.step3_complete:
                st.sidebar.success("Step 3: Newsletter Generated ✓")
                logger.info("Sidebar status: Step 3 complete")
            elif st.session_state.step2_complete:
                st.sidebar.info("Step 3: Generate Newsletter")
                logger.info("Sidebar status: Step 3 in progress")
            else:
                st.sidebar.text("Step 3: Generate Newsletter")
                logger.info("Sidebar status: Step 3 pending")