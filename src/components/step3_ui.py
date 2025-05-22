# app/components/step3_ui.py
import base64
import time
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger("tamu_newsletter")

class Step3UI:
    """UI component for Step 3: Generating Newsletter"""
    
    def __init__(self, generate_callback: Callable):
        """
        Initialize the Step 3 UI
        
        Args:
            generate_callback: Callback function to execute when newsletter generation is triggered
        """
        self.generate_callback = generate_callback
    
    def render(self):
        """Render the Step 3 UI components"""
        # Import streamlit only when needed, not at module level
        import streamlit as st
        
        st.header("Step 3: Generate Newsletter")
        logger.info("Step 3 header rendered")
        
        # Only show Step 3 if Step 2 is complete and Step 3 is not complete
        if st.session_state.step2_complete and not st.session_state.step3_complete:
            logger.info("Rendering Step 3 UI elements")
            
            # Run newsletter generation button
            if st.button("Generate Newsletter"):
                logger.info("Generate Newsletter button clicked")
                
                with st.spinner("Generating newsletter... This may take a few moments."):
                    # Call the generate callback (debug_mode removed)
                    self.generate_callback()
        
        # Display the generated newsletter if Step 3 is complete
        self._display_newsletter_if_complete()
    
    def _display_newsletter_if_complete(self):
        """Display the generated newsletter if Step 3 is complete"""
        # Import streamlit only when needed
        import streamlit as st
        
        if st.session_state.step2_complete and st.session_state.step3_complete:
            logger.info("Displaying generated newsletter")
            
            # Show the newsletter in an HTML component
            st.subheader("Generated Newsletter")
            
            # Option to view the HTML source
            show_source = st.checkbox("Show HTML Source")
            
            if show_source:
                # Display HTML source in a code block
                st.code(st.session_state.html_content, language="html")
            else:
                # Display rendered newsletter in an iframe
                html_display = st.empty()
                html_display.markdown(
                    f'<iframe src="data:text/html;base64,{base64.b64encode(st.session_state.html_content.encode()).decode()}" width="100%" height="800" style="border:none;"></iframe>', 
                    unsafe_allow_html=True
                )
            
            # Download button for the newsletter
            st.download_button(
                label="Download Newsletter HTML",
                data=st.session_state.html_content,
                file_name="tamu_cte_newsletter.html",
                mime="text/html"
            )
            
            # Provide instructions on using the newsletter
            st.info("""
            ### How to Use This Newsletter
            
            1. Download the HTML file using the button above
            2. You can send this HTML file directly as an email in many email clients
            3. For mass mailings, you can upload this template to your email marketing system
            4. For testing, you can open the downloaded file in any web browser
            """)
            
            # Option to restart generation
            if st.button("Regenerate Newsletter"):
                logger.info("User requested to regenerate newsletter")
                st.session_state.step3_complete = False
                st.rerun()