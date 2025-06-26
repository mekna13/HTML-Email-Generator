# app/components/event_editor.py
import streamlit as st
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("tamu_newsletter")

class EventEditor:
    """Component for editing scraped event data"""
    
    def __init__(self):
        """Initialize the event editor"""
        # Import data persistence utility
        try:
            from utils.data_persistence import DataPersistence
            self.data_persistence = DataPersistence()
        except ImportError:
            self.data_persistence = None
            logger.warning("DataPersistence not available - file operations disabled")
    
    def render_editor(self, events_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render the event editor interface
        
        Args:
            events_data: Dictionary containing CTE and ELP events
            
        Returns:
            Updated events data
        """
        st.subheader("📝 Review and Edit Events")
        st.info("Review the scraped events below. You can edit missing or incorrect information before proceeding to categorization.")
        
        # Create tabs for Summary, CTE and ELP events (Summary first and leftmost)
        summary_tab, cte_tab, elp_tab = st.tabs(["Summary", "CTE Events", "ELP Events"])
        
        # Store original data for comparison
        original_events_data = {
            "cte_events": events_data.get("cte_events", []).copy() if events_data.get("cte_events") else [],
            "elp_events": events_data.get("elp_events", []).copy() if events_data.get("elp_events") else []
        }
        
        # Summary tab (first and default)
        with summary_tab:
            self._render_summary(events_data)
        
        # Edit CTE events
        with cte_tab:
            events_data["cte_events"] = self._render_event_section(
                events_data.get("cte_events", []), 
                "CTE", 
                "cte"
            )
        
        # Edit ELP events
        with elp_tab:
            events_data["elp_events"] = self._render_event_section(
                events_data.get("elp_events", []), 
                "ELP", 
                "elp"
            )
        
        # Auto-save only if data actually changed
        data_changed = (
            events_data["cte_events"] != original_events_data["cte_events"] or
            events_data["elp_events"] != original_events_data["elp_events"]
        )
        
        if data_changed and self.data_persistence:
            self.data_persistence.save_events_data(events_data, create_backup=False)
            logger.info("Auto-saved changes to file")
        
        return events_data
    
    def _render_event_section(self, events_list: List[Dict], section_name: str, section_key: str) -> List[Dict]:
        """
        Render editing interface for a section of events
        
        Args:
            events_list: List of events to edit
            section_name: Display name for the section
            section_key: Key for the section (used in form keys)
            
        Returns:
            Updated events list
        """
        if not events_list:
            st.write(f"No {section_name} events found in the specified date range.")
            return events_list
        
        st.write(f"**{len(events_list)} {section_name} events found**")
        
        # Simple filter options
        filter_option = st.selectbox(
            "Show events:",
            ["All Events", "Events Missing Data", "Complete Events"],
            key=f"filter_{section_key}"
        )
        
        # Filter events based on selection
        filtered_events = []
        display_indices = []
        
        for i, event in enumerate(events_list):
            missing_fields = self._get_missing_fields(event)
            has_missing = len(missing_fields) > 0
            
            if filter_option == "All Events":
                filtered_events.append(event)
                display_indices.append(i)
            elif filter_option == "Events Missing Data" and has_missing:
                filtered_events.append(event)
                display_indices.append(i)
            elif filter_option == "Complete Events" and not has_missing:
                filtered_events.append(event)
                display_indices.append(i)
        
        if not filtered_events:
            st.write(f"No events match the '{filter_option}' filter.")
            return events_list
        
        st.write(f"Showing {len(filtered_events)} of {len(events_list)} events")
        
        # Show summary of what we're displaying
        missing_count = len([e for e in filtered_events if self._get_missing_fields(e)])
        complete_count = len(filtered_events) - missing_count
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Complete", complete_count)
        with col2:
            st.metric("Missing Data", missing_count)
        
        # IMPORTANT: Work with a copy to avoid reference issues
        updated_events = [event.copy() for event in events_list]
        
        # Edit each event
        for display_idx, original_idx in enumerate(display_indices):
            event = filtered_events[display_idx]
            
            # Get the current missing fields status for THIS specific event
            current_missing_fields = self._get_missing_fields(event)
            
            # Simple expander with status icon - calculate fresh each time
            status_icon = "⚠️" if current_missing_fields else "✅"
            title = f"{status_icon} {event.get('event_name', 'Unnamed Event')}"
            
            # Expand if has missing fields
            with st.expander(title, expanded=bool(current_missing_fields)):
                # Show what's missing at the top
                if current_missing_fields:
                    st.warning(f"⚠️ Missing: {', '.join(current_missing_fields)}")
                
                # Render the editor and get the updated event
                updated_event = self._render_single_event_editor(event, section_key, original_idx)
                
                # Only update if the event actually changed
                if updated_event != event:
                    updated_events[original_idx] = updated_event
                    logger.info(f"Event {original_idx} in {section_name} was updated")
        
        return updated_events
    
    def _render_single_event_editor(self, event: Dict[str, Any], section_key: str, event_idx: int) -> Dict[str, Any]:
        """Render editor for a single event"""
        
        # Work with a copy to avoid modifying the original
        current_event = event.copy()
        
        # Create form for this event with unique key
        form_key = f"event_form_{section_key}_{event_idx}_{hash(str(event))}"
        
        with st.form(form_key):
            # Basic event info
            col1, col2 = st.columns(2)
            
            with col1:
                event_name = st.text_input(
                    "Event Name *", 
                    value=current_event.get('event_name', ''),
                    key=f"name_{section_key}_{event_idx}_{hash(str(event))}"
                )
                
                event_date = st.text_input(
                    "Event Date *", 
                    value=current_event.get('event_date', ''),
                    key=f"date_{section_key}_{event_idx}_{hash(str(event))}"
                )
                
                event_time = st.text_input(
                    "Event Time *", 
                    value=current_event.get('event_time', ''),
                    key=f"time_{section_key}_{event_idx}_{hash(str(event))}"
                )
            
            with col2:
                event_location = st.text_input(
                    "Event Location", 
                    value=current_event.get('event_location', ''),
                    key=f"location_{section_key}_{event_idx}_{hash(str(event))}"
                )
                
                event_link = st.text_input(
                    "Event Link", 
                    value=current_event.get('event_link', ''),
                    key=f"link_{section_key}_{event_idx}_{hash(str(event))}"
                )
                
                event_registration_link = st.text_input(
                    "Registration Link", 
                    value=current_event.get('event_registration_link', ''),
                    key=f"reg_link_{section_key}_{event_idx}_{hash(str(event))}"
                )
            
            # Facilitators section
            st.subheader("Facilitators")
            event_facilitators = st.text_area(
                "Event Facilitators", 
                value=current_event.get('event_facilitators', ''),
                height=80,
                help="Enter facilitator names, separated by line breaks or commas",
                key=f"facilitators_{section_key}_{event_idx}_{hash(str(event))}",
                label_visibility="collapsed"
            )
            
            # Option to remove facilitators field if empty
            if not event_facilitators.strip():
                remove_facilitators = st.checkbox(
                    "🗑️ Remove facilitators field (no facilitator information available)",
                    key=f"remove_facilitators_{section_key}_{event_idx}_{hash(str(event))}",
                    help="Remove the facilitators field entirely from this event"
                )
            else:
                remove_facilitators = False
            
            # Description section
            st.subheader("Description")
            event_description = st.text_area(
                "Event Description", 
                value=current_event.get('event_description', ''),
                height=120,
                help="Enter or edit the event description",
                key=f"description_{section_key}_{event_idx}_{hash(str(event))}",
                label_visibility="collapsed"
            )
            
            # Option to remove description field if empty
            if not event_description.strip():
                remove_description = st.checkbox(
                    "🗑️ Remove description field (no description available)",
                    key=f"remove_description_{section_key}_{event_idx}_{hash(str(event))}",
                    help="Remove the description field entirely from this event"
                )
            else:
                remove_description = False
            
            # Submit button
            submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
            
            if submitted:
                # Build the updated event based on form inputs
                updated_event = {
                    'event_name': event_name,
                    'event_link': event_link,
                    'event_date': event_date,
                    'event_time': event_time,
                    'event_location': event_location,
                }
                
                # Only include registration link if not empty
                if event_registration_link.strip():
                    updated_event['event_registration_link'] = event_registration_link
                
                # Only include facilitators if not empty and not marked for removal
                if event_facilitators.strip() and not remove_facilitators:
                    updated_event['event_facilitators'] = event_facilitators
                
                # Only include description if not empty and not marked for removal  
                if event_description.strip() and not remove_description:
                    updated_event['event_description'] = event_description
                
                # Check if the event actually changed
                if updated_event != current_event:
                    st.success("✅ Event saved!")
                    logger.info(f"Updated event: {event_name}")
                    
                    # Update session state immediately and specifically
                    if hasattr(st.session_state, 'events_data') and st.session_state.events_data:
                        if section_key == 'cte':
                            if event_idx < len(st.session_state.events_data.get('cte_events', [])):
                                st.session_state.events_data['cte_events'][event_idx] = updated_event
                        elif section_key == 'elp':
                            if event_idx < len(st.session_state.events_data.get('elp_events', [])):
                                st.session_state.events_data['elp_events'][event_idx] = updated_event
                        
                        # Save to file immediately
                        if self.data_persistence:
                            self.data_persistence.save_events_data(st.session_state.events_data, create_backup=False)
                            logger.info("Saved individual event changes to file")
                    
                    # Return the updated event and force refresh
                    st.rerun()
                else:
                    st.info("ℹ️ No changes detected.")
                
                return updated_event
        
        # Return the current event if no changes were submitted
        return current_event
    
    def _render_summary(self, events_data: Dict[str, Any]):
        """Render overall summary of all events"""
        
        cte_events = events_data.get("cte_events", [])
        elp_events = events_data.get("elp_events", [])
        
        st.subheader("📊 Overall Summary")
        
        # Calculate statistics
        total_cte = len(cte_events)
        total_elp = len(elp_events)
        total_events = total_cte + total_elp
        
        complete_cte = len([e for e in cte_events if not self._get_missing_fields(e)])
        complete_elp = len([e for e in elp_events if not self._get_missing_fields(e)])
        total_complete = complete_cte + complete_elp
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Events", total_events)
        
        with col2:
            st.metric("CTE Events", total_cte)
        
        with col3:
            st.metric("ELP Events", total_elp)
        
        with col4:
            completion_rate = (total_complete / total_events * 100) if total_events > 0 else 0
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        # Show completion status
        if total_complete == total_events:
            st.success("🎉 All events have complete information!")
        else:
            missing_count = total_events - total_complete
            st.info(f"ℹ️ {missing_count} events have optional fields that could be filled in.")
        
        # Show date range
        if events_data.get("date_range"):
            date_range = events_data["date_range"]
            st.info(f"📅 Date Range: {date_range.get('start_date')} to {date_range.get('end_date')}")
        
        # Show detailed breakdown
        st.subheader("📋 Event List")
        
        # Create summary table
        summary_data = []
        
        for event_type, events in [("CTE", cte_events), ("ELP", elp_events)]:
            for i, event in enumerate(events):
                missing_fields = self._get_missing_fields(event)
                
                summary_data.append({
                    "Type": event_type,
                    "Event Name": self._truncate_text(event.get('event_name', 'Unnamed Event'), 50),
                    "Date": event.get('event_date', ''),
                    "Facilitators": "✅" if 'event_facilitators' in event and event.get('event_facilitators') else "—",
                    "Description": "✅" if 'event_description' in event and event.get('event_description') else "—",
                    "Registration": "✅" if 'event_registration_link' in event and event.get('event_registration_link') else "—",
                    "Status": "✅ Complete" if not missing_fields else f"Optional: {', '.join(missing_fields)}"
                })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True)
            
        st.info("ℹ️ Events with missing optional fields (Facilitators, Description, Registration) can still be used for newsletter generation.")
    
    def _get_missing_fields(self, event: Dict[str, Any]) -> List[str]:
        """Get list of missing optional fields for an event (simplified logic)"""
        missing = []
        
        # Only consider fields as "missing" if they exist but are empty
        # If fields are completely absent, they were intentionally removed
        
        # Check facilitators - only missing if field exists and is empty
        if 'event_facilitators' in event:
            if not event.get('event_facilitators', '').strip():
                missing.append("Facilitators")
        
        # Check description - only missing if field exists and is empty
        if 'event_description' in event:
            if not event.get('event_description', '').strip():
                missing.append("Description")
        
        # Check registration link - only missing if field exists and is empty
        if 'event_registration_link' in event:
            if not event.get('event_registration_link', '').strip():
                missing.append("Registration")
        
        return missing
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to specified length with ellipsis"""
        if not text:
            return ""
        
        return text[:max_length] + "..." if len(text) > max_length else text
    
    def _clean_empty_fields(self, events_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove empty fields from all events"""
        
        def clean_event(event: Dict[str, Any]) -> Dict[str, Any]:
            """Clean empty fields from a single event"""
            cleaned_event = event.copy()
            
            # Fields that can be removed if empty
            removable_fields = [
                'event_facilitators',
                'event_description', 
                'event_registration_link'
            ]
            
            for field in removable_fields:
                if field in cleaned_event:
                    value = cleaned_event[field]
                    # Remove if empty, None, or just whitespace
                    if not value or (isinstance(value, str) and not value.strip()):
                        del cleaned_event[field]
                        logger.info(f"Removed empty field '{field}' from event: {cleaned_event.get('event_name', 'Unknown')}")
            
            return cleaned_event
        
        # Clean CTE events
        if 'cte_events' in events_data:
            events_data['cte_events'] = [clean_event(event) for event in events_data['cte_events']]
        
        # Clean ELP events  
        if 'elp_events' in events_data:
            events_data['elp_events'] = [clean_event(event) for event in events_data['elp_events']]
        
        return events_data