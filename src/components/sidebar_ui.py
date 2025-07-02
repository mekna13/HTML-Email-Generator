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
            
            # Google Sheets status
            st.sidebar.write("---")
            st.sidebar.write("### 📊 Google Sheets Cache")
            
            self._display_google_sheets_status()
    
    def _display_google_sheets_status(self):
        """Display Google Sheets connection status and URL"""
        import streamlit as st
        
        try:
            from services.categorizer import EventCategorizer
            categorizer = EventCategorizer()
            sheets_url = categorizer.get_spreadsheet_url()
            
            if sheets_url:
                st.sidebar.success("✅ Connected")
                
                # Single markdown link that opens in new tab
                st.sidebar.markdown(f"""
                <a href="{sheets_url}" target="_blank" style="
                    display: inline-block;
                    padding: 0.25rem 0.75rem;
                    background-color: #ff4b4b;
                    color: white;
                    text-decoration: none;
                    border-radius: 0.25rem;
                    font-weight: 500;
                    text-align: center;
                    width: 100%;
                    box-sizing: border-box;
                ">
                📊 Open Google Sheets
                </a>
                """, unsafe_allow_html=True)
                
                # Show helpful info
                st.sidebar.caption("💡 Edit categories manually")
                
                logger.info(f"Sidebar displaying Google Sheets URL: {sheets_url}")
            else:
                st.sidebar.warning("⚠️ Not Connected")
                st.sidebar.caption("Run categorization to create cache")
                
        except Exception as e:
            st.sidebar.error("❌ Connection Error")
            st.sidebar.caption(f"Error: {str(e)[:50]}...")
            logger.error(f"Sidebar Google Sheets error: {e}")