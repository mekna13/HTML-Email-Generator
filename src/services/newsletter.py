# app/services/newsletter.py
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import gspread
from google.oauth2.service_account import Credentials

# Get logger
logger = logging.getLogger("tamu_newsletter")

class NewsletterGenerator:
    """
    Service class to handle newsletter generation functionality with Google Sheets integration
    """
    
    def __init__(self):
        """Initialize the newsletter generator with Google Sheets integration"""
        self.categorized_events_path = "categorized_events.json"
        self.newsletter_output_path = "newsletter.html"
        
        # Google Sheets configuration (same as categorizer)
        self.spreadsheet_name = "TAMU Newsletter Cache v3"
        self.sheets_config = {
            "categorization_cache": "Categorization Cache"
        }
        
        # Initialize Google Sheets client
        self.gc = None
        self.spreadsheet = None
        self._initialize_sheets_client()
    
    def _initialize_sheets_client(self):
        """Initialize Google Sheets client with service account credentials"""
        try:
            # Define the scope
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Get credentials from Streamlit secrets
            import streamlit as st
            credentials_dict = dict(st.secrets["gcp_service_account"])
            credentials = Credentials.from_service_account_info(credentials_dict, scopes=scope)
            logger.info("Using credentials from Streamlit secrets")
            
            # Initialize the client
            self.gc = gspread.authorize(credentials)
            
            # Try to open existing spreadsheet
            try:
                self.spreadsheet = self.gc.open(self.spreadsheet_name)
                logger.info(f"Opened existing spreadsheet: {self.spreadsheet_name}")
            except gspread.SpreadsheetNotFound:
                logger.warning(f"Spreadsheet '{self.spreadsheet_name}' not found. Newsletter generation will continue without cache.")
                self.spreadsheet = None
            
        except Exception as e:
            logger.warning(f"Failed to initialize Google Sheets client: {e}")
            logger.info("Newsletter generation will continue without Google Sheets cache")
            self.gc = None
            self.spreadsheet = None
    
    def _get_sheet(self, sheet_key: str):
        """Get a specific sheet by key"""
        if not self.spreadsheet:
            return None
            
        sheet_name = self.sheets_config.get(sheet_key)
        if not sheet_name:
            return None
            
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            logger.warning(f"Sheet not found: {sheet_name}")
            return None
    
    def _load_categorization_cache_from_sheets(self) -> Dict[str, Dict[str, List[str]]]:
        """Load categorization cache from Google Sheets"""
        if not self.spreadsheet:
            logger.warning("No Google Sheets connection available")
            return {"CTE": {}, "ELP": {}}
        
        try:
            sheet = self._get_sheet("categorization_cache")
            if not sheet:
                logger.warning("Categorization cache sheet not found")
                return {"CTE": {}, "ELP": {}}
            
            records = sheet.get_all_records()
            cache = {"CTE": {}, "ELP": {}}
            
            for record in records:
                event_type = record.get('Event Type', '').strip()
                category_name = record.get('Category Name', '').strip()
                event_titles_str = record.get('Event Titles', '').strip()
                
                if event_type in ['CTE', 'ELP'] and category_name and event_titles_str:
                    try:
                        event_titles = json.loads(event_titles_str)
                        cache[event_type][category_name] = event_titles
                    except json.JSONDecodeError:
                        # Fallback: split by newlines
                        event_titles = [title.strip() for title in event_titles_str.split('\n') if title.strip()]
                        cache[event_type][category_name] = event_titles
            
            logger.info(f"Loaded categorization cache from Google Sheets: {len(cache['CTE'])} CTE categories, {len(cache['ELP'])} ELP categories")
            return cache
            
        except Exception as e:
            logger.error(f"Error loading categorization cache from Google Sheets: {e}")
            return {"CTE": {}, "ELP": {}}
    
    def generate_newsletter(self, debug_mode: bool = False) -> Tuple[bool, str]:
        """
        Generate newsletter HTML from categorized events
        
        Args:
            debug_mode: Whether to run in debug mode (ignored now - always runs directly)
            
        Returns:
            Tuple of (success, html_content)
        """
        logger.info("Starting newsletter generation")
        
        # Check if required files exist
        import os
        if not os.path.exists(self.categorized_events_path):
            error_msg = f"Categorized events file not found: {self.categorized_events_path}"
            logger.error(error_msg)
            return (False, error_msg)
        
        # Always run directly now - no subprocess needed
        return self._generate_direct()
    
    def _generate_direct(self) -> Tuple[bool, str]:
        """
        Run newsletter generation directly with integrated functionality
        
        Returns:
            Tuple of (success, html_content)
        """
        logger.info("Running newsletter generation directly with integrated functionality")
        
        try:
            # Load categorization cache from Google Sheets
            categorization_cache = self._load_categorization_cache_from_sheets()
            
            # Generate HTML content
            logger.info("Generating HTML content")
            html_content = self._generate_email_html(
                self.categorized_events_path, 
                categorization_cache
            )
            
            # Save the newsletter to file
            with open(self.newsletter_output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            logger.info(f"Newsletter saved to {self.newsletter_output_path}")
            
            return (True, html_content)
            
        except Exception as e:
            logger.error(f"Error during newsletter generation: {str(e)}", exc_info=True)
            return (False, f"Error during newsletter generation: {str(e)}")
        
    
    def _distribute_weekly_events(self, regular_categories: List[Dict], weekly_events: List[Dict]) -> List[Dict]:
        """
        Distribute weekly events evenly between regular event categories
        
        Args:
            regular_categories: List of regular event categories
            weekly_events: List of weekly events
            
        Returns:
            List with weekly events distributed between regular categories
        """
        if not weekly_events:
            return [{"type": "regular", "data": event} for event in regular_categories]
        
        if not regular_categories:
            # If no regular categories, return weekly events as is
            return [{"type": "weekly", "data": event} for event in weekly_events]
        
        # Calculate distribution points
        total_regular = len(regular_categories)
        total_weekly = len(weekly_events)
        
        # Distribute weekly events evenly
        distributed_content = []
        weekly_index = 0
        
        for i, category in enumerate(regular_categories):
            # Add the regular category
            distributed_content.append({"type": "regular", "data": category})
            
            # Calculate if we should add a weekly event after this category
            # We want to distribute weekly events as evenly as possible
            if weekly_index < total_weekly:
                # Use a distribution formula to space weekly events evenly
                position_ratio = (i + 1) / total_regular
                expected_weekly_position = position_ratio * total_weekly
                
                if weekly_index < expected_weekly_position:
                    distributed_content.append({"type": "weekly", "data": weekly_events[weekly_index]})
                    weekly_index += 1
        
        # Add any remaining weekly events at the end
        while weekly_index < total_weekly:
            distributed_content.append({"type": "weekly", "data": weekly_events[weekly_index]})
            weekly_index += 1
        
        return distributed_content
    
    def _generate_email_html(self, categorized_events_path: str, categorization_cache: Dict[str, Dict[str, List[str]]]) -> str:
        """Generate the complete HTML newsletter"""
        # Load the JSON data
        with open(categorized_events_path, 'r') as f:
            categorized_events = json.load(f)
        
        # Extract data
        date_range = categorized_events.get('date_range', {})
        cte_events = categorized_events.get('cte_events', [])
        elp_events = categorized_events.get('elp_events', [])
        weekly_events = categorized_events.get('weekly_events', [])
        
        logger.info(f"Processing {len(cte_events)} CTE categories, {len(elp_events)} ELP categories, {len(weekly_events)} weekly events")
        logger.info(f"Categorization cache contains: {len(categorization_cache.get('CTE', {}))} CTE categories, {len(categorization_cache.get('ELP', {}))} ELP categories")
        
        # Start building the HTML
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Center for Teaching Excellence Newsletter</title>
</head>
<body>
    <div align="center">
        <table border="0" cellspacing="0" cellpadding="0" width="600" style="width:6.25in;color:inherit;font-size:inherit">
            <tbody>
                <tr>
                    <td style="padding:7.5pt 0in 7.5pt 0in">
                        <div align="center">
                            <table border="0" cellspacing="0" cellpadding="0" width="600" style="width:6.25in;color:inherit;font-size:inherit">
                                <tbody>
                                    <tr>
                                        <td style="padding:0in 0in 0in 0in">
                                            <p class="MsoNormal" align="center" style="text-align:center">
                                                <img width="600" height="100" style="width:6.25in;height:1.0416in" src="https://cte.tamu.edu/getmedia/34eb76b6-4b5f-4834-a7a0-257b97fd7231/CTE_Email_Header.jpg" alt="square texas a and m logo on an off white marble background with words texas a and m university center for teaching excellence">
                                            </p>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div align="center">
                            <table border="0" cellspacing="0" cellpadding="0" width="600" style="width:6.25in;color:inherit;font-size:inherit">
                                <tbody>
                                    <tr>
                                        <td style="background:#500000;padding:7.5pt 11.25pt 7.5pt 3.75pt">
                                            <h1>
                                                <span style="font-size:12.0pt;font-family:&quot;Open Sans&quot;,sans-serif;color:white;font-weight:bold">UPCOMING OFFERINGS AT THE CENTER FOR TEACHING EXCELLENCE</span><span style="font-weight:normal"><u></u><u></u></span>
                                            </h1>
                                            <p class="MsoNormal">
                                                <span style="font-size:10.0pt;font-family:&quot;Open Sans&quot;,sans-serif;color:white">The Center for Teaching Excellence is dedicated to fostering innovation in education through cutting-edge methodologies and technology integration. With a mission to empower educators, the center provides dynamic resources, workshops, and seminars to elevate teaching practices and ultimately enrich the learning experience for students. Check out our upcoming offerings below.</span><u></u><u></u>
                                            </p>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <p class="MsoNormal">
                            <span style="display:none"><u></u>&nbsp;<u></u></span>
                        </p>
        """
        
        # Create distributed content for CTE section
        cte_distributed = self._distribute_weekly_events(cte_events, weekly_events[:len(weekly_events)//2])
        
        # Process CTE events with distributed weekly events
        for item in cte_distributed:
            print(item)  # Debugging line to check item structure
            if item["type"] == "regular" and item["data"]["category_name"] != "Additional Events":
                category = item["data"]
                category_name = category.get('category_name', '')
                category_description = category.get('description', '')
                events = category.get('events', [])
                
                # Add category title and description
                html += self._category_template(category_name, category_description)
                
                # Add each event in the category
                for event in events:
                    html += self._event_template(event)
                
                # Add separator after category
                html += self._separator_template()
            
            elif item["type"] == "weekly":
                weekly_data = item["data"]
                if isinstance(weekly_data, dict):
                    weekly_data = [weekly_data]

                for weekly_event in weekly_data:
                    html += self._weekly_event_template(weekly_event)

        # NOW process any "Additional Events" categories for CTE (at the end)
        for item in cte_distributed:
            if item["type"] == "regular" and item["data"]["category_name"] == "Additional Events":
                category = item["data"]
                html += self._category_template(category["category_name"], category.get("description", ""))
                for event in category.get("events", []):
                    html += self._event_template(event)
                html += self._separator_template()

        # Add ELP banner before ELP events
        html += """
                            <table border="0" cellspacing="0" cellpadding="0" width="600" style="width:6.25in;color:inherit;font-size:inherit">
                                <tbody>
                                    <tr>
                                        <td style="padding:0in 0in 0in 0in">
                                            <p class="MsoNormal" align="center" style="text-align:center">
                                                <img border="0" width="600" height="191" style="width:6.25in;height:1.9895in" src="https://cte.tamu.edu/getmedia/d05bda8d-4017-47a3-9d07-26a966d9da55/ELP_Title_Banner.png" alt="image of two students studying outdoors with English language proficiency workshops superimposed in a maroon bar">
                                            </p>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
        """
        
        # Create distributed content for ELP section
        remaining_weekly = weekly_events[len(weekly_events)//2:]
        elp_distributed = self._distribute_weekly_events(elp_events, remaining_weekly)
        
        # Process ELP events with distributed weekly events
        for item in elp_distributed:
            
            if item["type"] == "regular":
                category = item["data"]
                category_name = category.get('category_name', '')
                category_description = category.get('description', '')
                events = category.get('events', [])
                
                # Add category title and description
                html += self._category_template(category_name, category_description)
                
                # Add each event in the category
                for event in events:
                    html += self._event_template(event)
                
                # Add separator after category
                html += self._separator_template()
            
            elif item["type"] == "weekly":
                weekly_event = item["data"]
                html += self._weekly_event_template(weekly_event)
                html += self._separator_template()
        
        # Add footer
        html += """
                            <div align="center">
                                <table border="0" cellspacing="0" cellpadding="0" width="600" style="width:6.25in;color:inherit;font-size:inherit">
                                    <tbody>
                                        <tr>
                                            <td style="padding:7.5pt 0in 7.5pt 0in">
                                                <p align="center" style="text-align:center">
                                                    <span style="font-size:10.0pt;font-family:&quot;Open Sans&quot;,sans-serif"><a href="https://ecomms.marcomm.tamu.edu/trk/click?ref=z177i6rteh_0-114_0x38e2x0314" style="text-decoration:underline;color:#500000" target="_blank"><b><span style="font-size:12.0pt;font-family:&quot;Open Sans&quot;,sans-serif;color:#500000">View the CTE Calendar for More Workshops and Events</span></b></a></span><u></u><u></u>
                                                </p>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            <p class="MsoNormal">
                                <span style="display:none"><u></u>&nbsp;<u></u></span>
                            </p>
                            <div align="center">
                                <table border="0" cellspacing="0" cellpadding="0" width="225" style="width:168.75pt;color:inherit;font-size:inherit">
                                    <tbody>
                                        <tr>
                                            <td width="75" style="width:56.25pt;padding:0in 0in 0in 0in">
                                                <p class="MsoNormal" align="center" style="text-align:center">
                                                    <a href="https://ecomms.marcomm.tamu.edu/trk/click?ref=z177i6rteh_0-114_0x38e3x0314" target="_blank"><span style="text-decoration:none"><img border="0" width="40" height="40" style="width:.4166in;height:.4166in" src="https://cte.tamu.edu/getmedia/c3e2b389-a15c-4e80-afd5-f62aa551bf91/icons8-linkedin-100.png" alt="LinkedIn Icon"></span></a><u></u><u></u>
                                                </p>
                                            </td>
                                            <td width="75" style="width:56.25pt;padding:0in 0in 0in 0in">
                                                <p class="MsoNormal" align="center" style="text-align:center">
                                                    <a href="https://ecomms.marcomm.tamu.edu/trk/click?ref=z177i6rteh_0-114_0x38e4x0314" target="_blank"><span style="text-decoration:none"><img border="0" width="40" height="40" style="width:.4166in;height:.4166in" src="https://cte.tamu.edu/getmedia/d92c50e1-0eb6-4f91-9e82-d8ef635cdc80/icons8-email-100.png" alt="Email Icon"></span></a><u></u><u></u>
                                                </p>
                                            </td>
                                            <td width="75" style="width:56.25pt;padding:0in 0in 0in 0in">
                                                <p class="MsoNormal" align="center" style="text-align:center">
                                                    <a href="https://ecomms.marcomm.tamu.edu/trk/click?ref=z177i6rteh_0-114_0x38e5x0314" target="_blank"><span style="text-decoration:none"><img border="0" width="40" height="40" style="width:.4166in;height:.4166in" src="https://cte.tamu.edu/getmedia/1af1f691-e15d-409f-886c-84d67e2d2e6b/294712_circle_youtube_icon.png" alt="Youtube Icon"></span></a><u></u><u></u>
                                                </p>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>
            """
        
        return html
    
    def _weekly_event_template(self, weekly_event: Dict[str, Any]) -> str:
        """Generate HTML for a weekly event using the provided template"""
        category_name = weekly_event.get('category_name', '')
        description = weekly_event.get('description', '')
        weekly_event_info = weekly_event.get('weekly_event_info', '')
        event_link = weekly_event.get('event_link', '')
        event_registration_link = weekly_event.get('event_registration_link', '')
        
        # Convert category name to all caps and add "WEEKLY SESSIONS"
        category_name_display = f"{category_name.upper()}: WEEKLY SESSIONS"
        
        # Use full category name for links (no shortening)
        category_name_for_links = category_name
        
        return f"""
                        <div align="center">
                            <table border="0" cellspacing="0" cellpadding="0" width="600"
                                style="width:6.25in;color:inherit;font-size:inherit">
                                <tbody>
                                    <tr>
                                        <td style="padding:7.5pt 0in 11.25pt 0in">
                                            <p>
                                                <b><span
                                                        style="font-size:10.0pt;font-family:&quot;Open Sans&quot;,sans-serif;color:#500000">{category_name_display}</span></b><span
                                                    style="font-size:10.0pt;font-family:&quot;Open Sans&quot;,sans-serif"><br>
                                                    <span style="color:#500000">{description}</span></span><u></u><u></u>
                                            </p>
                                            <p>
                                                <span
                                                    style="font-size:10.0pt;font-family:&quot;Open Sans&quot;,sans-serif;color:#500000">{weekly_event_info}</span><span
                                                    style="font-size:10.0pt;font-family:&quot;Open Sans&quot;,sans-serif"><br>
                                                    <span style="color:#500000"><b><a
                                                            href="{event_link}"
                                                            target="_blank"
                                                            style="color:#500000">Read more about the
                                                            {category_name_for_links} Sessions
                                                            here</a></b>.<br>
                                                        <b><a href="{event_registration_link}"
                                                            target="_blank"
                                                            style="color:#500000">Register for the
                                                            {category_name_for_links}
                                                            here</a></b>.</span></span><u></u><u></u>
                                            </p>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
        """
    
    def _category_template(self, category_name: str, category_description: str) -> str:
        """Generate HTML for category title and description"""
        # If category_name is "Additional Events", do not include category_description
        if category_name.strip().lower() == "additional events":
            category_name = category_name + ":"
            return f"""
                    <div align="center">
                    <table border="0" cellspacing="0" cellpadding="0" width="600" style="width:6.25in;color:inherit;font-size:inherit">
                        <tbody>
                        <tr>
                            <td style="padding:7.5pt 0in 11.25pt 0in">
                            <p>
                                <b><span style="font-size:10.0pt;font-family:&quot;Open Sans&quot;,sans-serif;color:#500000">{category_name}
                                   </span></b><u></u><u></u>
                            </p>
                            </td>
                        </tr>
                        </tbody>
                    </table>
                    </div>
            """
        else:
            return f"""
                    <div align="center">
                    <table border="0" cellspacing="0" cellpadding="0" width="600" style="width:6.25in;color:inherit;font-size:inherit">
                        <tbody>
                        <tr>
                            <td style="padding:7.5pt 0in 11.25pt 0in">
                            <p>
                                <b><span style="font-size:10.0pt;font-family:&quot;Open Sans&quot;,sans-serif;color:#500000">{category_name}
                                   </span></b><span style="font-size:10.0pt;font-family:&quot;Open Sans&quot;,sans-serif;color:#500000">
                                {category_description}</span><u></u><u></u>
                            </p>
                            </td>
                        </tr>
                        </tbody>
                    </table>
                    </div>
            """
    
    def _event_template(self, event: Dict[str, Any]) -> str:
        """Generate HTML for an individual event with HTML calendar icon"""
        
        # Extract event details
        event_name = event.get('event_name', '')
        event_link = event.get('event_link', '')
        event_date = event.get('event_date', '')
        event_time = event.get('event_time', '')
        # Ensure AM/PM is uppercase
        if isinstance(event_time, str):
            event_time = event_time.replace('am', ' AM').replace('pm', ' PM')
        event_location = event.get('event_location', '')
        event_facilitators = event.get('event_facilitators', '')
        event_description = event.get('event_description', '')
        event_registration_link = event.get('event_registration_link', '')
        
        # Convert event title to uppercase
        event_name_uppercase = event_name.upper()
        
        # Parse date to extract day and month for calendar icon
        calendar_day, calendar_month = self._parse_date_for_calendar(event_date)
        
        # Use full event name for links (no shortening)
        event_name_for_links = event_name
        
        # Build the description section conditionally
        description_parts = []
        
        # Always include date and location
        description_parts.append(f"{event_date}, {event_location}<br>")
        
        # Check if we have facilitators or description to determine if we need <br> after time
        has_facilitators = event_facilitators and event_facilitators.strip()
        has_description = event_description and event_description.strip()
        has_additional_content = has_facilitators or has_description
        
        # Add time with conditional <br>
        if has_additional_content:
            description_parts.append(f"Time: {event_time}<br>")  # Add <br> if more content follows
        else:
            description_parts.append(f"Time: {event_time}")      # No <br> if this is the last item
        
        # Conditionally add facilitators if they exist
        if has_facilitators:
            if has_description:
                # Add <br> after facilitators if description follows
                description_parts.append(f"<b>Facilitators</b>: {event_facilitators}<br>")
            else:
                # No <br> after facilitators if it's the last item
                description_parts.append(f"<b>Facilitators</b>: {event_facilitators}")
        
        # Conditionally add description if it exists (never needs <br> as it's always last)
        if has_description:
            description_parts.append(f"<b>Description</b>: {event_description}")
        
        # Join all parts together
        description_html = "".join(description_parts)
        
        return f"""
            <div align="center">
                <table border="0" cellspacing="0" cellpadding="0" width="600" style="width:6.25in;color:inherit;font-size:inherit">
                    <tbody>
                        <tr>
                            <td width="45" valign="top" style="width:33.75pt;padding:3.75pt 3.75pt 0in 0in">
                                <p class="MsoNormal" align="center" style="text-align:center">
                                    <table border="0" cellspacing="0" cellpadding="0" style="width:41px;height:43px;background-color:#500000;">
                                        <tr>
                                            <td style="text-align:center;vertical-align:middle;font-family:'Open Sans',Arial,sans-serif;color:white;padding:0;line-height:1;">
                                                <div style="font-size:16px;font-weight:bold;">{calendar_day}</div>
                                                <div style="font-size:8px;font-weight:bold;margin-top:2px;">{calendar_month}</div>
                                            </td>
                                        </tr>
                                    </table>
                                    <u></u><u></u>
                                </p>
                            </td>
                            <td valign="top" style="padding:0in 0in 11.25pt 0in">
                                <p class="MsoNormal">
                                    <b><a href="{event_link}" style="text-decoration:underline;color:#500000" target="_blank"><span style="font-size:9.0pt;font-family:&quot;Open Sans&quot;,sans-serif;color:#500000">{event_name_uppercase}</span></a></b><br>
                                    <span style="font-size:9.0pt;font-family:&quot;Open Sans&quot;,sans-serif">{description_html}</span><br>
                                    <b><span style="font-size:9.0pt;font-family:&quot;Open Sans&quot;,sans-serif"><a href="{event_link}" style="text-decoration:underline;color:#500000" target="_blank"><span style="font-family:&quot;Open Sans&quot;,sans-serif;color:#500000">Read more about the {event_name_for_links} event here</span></a></span></b><span style="font-size:9.0pt;font-family:&quot;Open Sans&quot;,sans-serif">.<br>
                                    <b><a href="{event_registration_link}" style="text-decoration:underline;color:#500000" target="_blank"><span style="font-family:&quot;Open Sans&quot;,sans-serif;color:#500000">Register for the {event_name_for_links} event here</span></a></b>.</span><u></u><u></u>
                                </p>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        """
    def _parse_date_for_calendar(self, event_date: str) -> tuple:
        """Parse event date string to extract day and month for calendar display"""
        
        import re
        from datetime import datetime
        
        try:
            # Handle different date formats
            # Example: "Monday, June 9, 2025" or "June 9, 2025"
            
            # Extract the date part (remove day name if present)
            date_part = event_date
            if ',' in event_date:
                parts = event_date.split(',')
                if len(parts) >= 2:
                    # If format is "Monday, June 9, 2025", take "June 9, 2025"
                    date_part = ','.join(parts[1:]).strip()
                
            # Try to parse common date formats
            date_formats = [
                "%B %d, %Y",  # "June 9, 2025"
                "%b %d, %Y",  # "Jun 9, 2025"
                "%m/%d/%Y",   # "6/9/2025"
                "%Y-%m-%d",   # "2025-06-09"
            ]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_part, fmt)
                    break
                except ValueError:
                    continue
            
            if parsed_date:
                day = str(parsed_date.day)
                month = parsed_date.strftime("%b").upper()[:3]  # Get 3-letter month abbreviation, ensure max 3 chars
                return day, month
            
            # Fallback: try to extract with regex
            # Look for day number and month name
            day_match = re.search(r'\b(\d{1,2})\b', date_part)
            month_match = re.search(r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', date_part, re.IGNORECASE)
            
            if day_match and month_match:
                day = day_match.group(1)
                month = month_match.group(1)[:3].upper()  # First 3 letters only, uppercase
                return day, month
                
        except Exception as e:
            # Log the error but don't break the template
            logger.warning(f"Error parsing date '{event_date}': {e}")
        
        # Fallback to generic calendar icon
        return "?", "???"
    
    def _separator_template(self) -> str:
        """Generate HTML for category separator"""
        return """
                            <table border="0" cellspacing="0" cellpadding="0" width="600" style="width:6.25in;color:inherit;font-size:inherit">
                                <tbody>
                                    <tr>
                                        <td style="padding:0in 0in 0in 0in">
                                            <p class="MsoNormal">
                                                <img border="0" width="600" height="29" style="width:6.25in;height:.302in" src="https://ci3.googleusercontent.com/meips/ADKq_NZou0fPXW1JRUPih89tqUwjW-HC6yjcfNK9Sy6WLL6Ugk8tDChFYugaW_bd7lkvlpW_AZidqqzPQnex04_V57egCu0Jcn7NHgmGdac_OWWc88KYbfm-AlrsO1XXd_Ud-CHYp7Ll5bQfFnY9XJQq_aByMBuVGvXib8Ht-PAoRaEQ_TrJ0_OqAe5I6lACj8RD=s0-d-e1-ft#https://maestro.marcomm.tamu.edu/list/img/pic?t=HTML_IMAGE&amp;j=250313G&amp;i=3mk8k2fb7iboa3ybsqs9wjxuchij4nfvi2a2wxta2ci71owmad" alt="two rows of gray dots as separator" class="CToWUd" data-bit="iit"><u></u><u></u>
                                            </p>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
        """