# app/utils/state_manager.py
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger("tamu_newsletter")

class StateManager:
    """
    Utility class to manage Streamlit session state
    """
    
    @staticmethod
    def initialize_states():
        """Initialize all required session states if they don't exist"""
        # Import streamlit only when needed, not at module level
        import streamlit as st
        
        # Step completion states
        if 'step1_complete' not in st.session_state:
            st.session_state.step1_complete = False
        if 'step2_complete' not in st.session_state:
            st.session_state.step2_complete = False
        if 'step3_complete' not in st.session_state:
            st.session_state.step3_complete = False
        
        # Data states
        if 'events_data' not in st.session_state:
            st.session_state.events_data = None
        if 'categorized_events' not in st.session_state:
            st.session_state.categorized_events = None
        if 'html_content' not in st.session_state:
            st.session_state.html_content = None
        
        logger.info("Session state initialized")
    
    @staticmethod
    def set_state(key: str, value: Any):
        """Set a value in the session state"""
        import streamlit as st
        st.session_state[key] = value
        logger.info(f"Set session state {key}")
    
    @staticmethod
    def get_state(key: str, default: Optional[Any] = None) -> Any:
        """Get a value from the session state with an optional default"""
        import streamlit as st
        value = st.session_state.get(key, default)
        return value
    
    @staticmethod
    def reset_state(key: str):
        """Reset a specific state value to its default"""
        import streamlit as st
        
        if key == 'step1_complete':
            st.session_state.step1_complete = False
        elif key == 'step2_complete':
            st.session_state.step2_complete = False
        elif key == 'step3_complete':
            st.session_state.step3_complete = False
        elif key == 'events_data':
            st.session_state.events_data = None
        elif key == 'categorized_events':
            st.session_state.categorized_events = None
        elif key == 'html_content':
            st.session_state.html_content = None
        else:
            # For any other key, just remove it from session state
            if key in st.session_state:
                del st.session_state[key]
        
        logger.info(f"Reset session state {key}")
    
    @staticmethod
    def reset_all_states():
        """Reset all session states to their defaults"""
        import streamlit as st
        
        st.session_state.step1_complete = False
        st.session_state.step2_complete = False
        st.session_state.step3_complete = False
        st.session_state.events_data = None
        st.session_state.categorized_events = None
        st.session_state.html_content = None
        
        logger.info("All session states reset")