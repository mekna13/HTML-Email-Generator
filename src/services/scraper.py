# app/services/scraper.py
import json
import datetime
import time
import re
from datetime import date
from typing import Dict, List, Any, Optional, Tuple
import logging

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from dateutil.parser import parse

# Get logger
logger = logging.getLogger("tamu_newsletter")

class EventScraper:
    """
    Service class to handle event scraping functionality
    """
    
    def __init__(self):
        """Initialize the event scraper"""
        self.cte_url = "https://calendar.tamu.edu/cte/all"
        self.elp_url = "https://calendar.tamu.edu/elp/all"
    
    def scrape_events(self, start_date: date, end_date: date, debug_mode: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Scrape events from TAMU calendars
        
        Args:
            start_date: Start date for event range
            end_date: End date for event range
            debug_mode: Whether to run in debug mode (ignored now - always runs directly)
            
        Returns:
            Tuple of (success, events_data)
        """
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        logger.info(f"Starting scraping for date range: {start_date_str} to {end_date_str}")
        
        # Always run directly now - no subprocess needed
        return self._scrape_direct(start_date, end_date)
    
    def _scrape_direct(self, start_date: date, end_date: date) -> Tuple[bool, Dict[str, Any]]:
        """
        Run scraping directly with integrated functionality
        
        Args:
            start_date: Start date for event range
            end_date: End date for event range
            
        Returns:
            Tuple of (success, events_data)
        """
        logger.info("Running scraping directly with integrated functionality")
        
        try:
            # Scrape CTE events
            logger.info(f"Scraping CTE events from {self.cte_url}")
            cte_events = []
            try:
                cte_events = self._scrape_events_from_url(self.cte_url, start_date, end_date)
                logger.info(f"Found {len(cte_events)} CTE events")
            except Exception as e:
                logger.error(f"Error scraping CTE events: {str(e)}")
                return (False, {"error": f"Error scraping CTE events: {str(e)}"})
            
            # Scrape ELP events
            logger.info(f"Scraping ELP events from {self.elp_url}")
            elp_events = []
            try:
                elp_events = self._scrape_events_from_url(self.elp_url, start_date, end_date)
                logger.info(f"Found {len(elp_events)} ELP events")
            except Exception as e:
                logger.error(f"Error scraping ELP events: {str(e)}")
                return (False, {"error": f"Error scraping ELP events: {str(e)}"})
            
            # Prepare and save the data
            events_data = {
                "date_range": {
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": end_date.strftime('%Y-%m-%d')
                },
                "cte_events": cte_events,
                "elp_events": elp_events
            }
            
            # Save data to file
            try:
                logger.info("Saving data to events.json")
                with open("events.json", "w", encoding="utf-8") as f:
                    json.dump(events_data, f, indent=2)
            except Exception as e:
                logger.error(f"Error saving events data to file: {str(e)}")
                return (False, {"error": f"Error saving events data: {str(e)}"})
            
            logger.info("Direct scraping completed successfully")
            return (True, events_data)
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return (False, {"error": f"Error during scraping: {str(e)}"})
    
    def _is_within_date_range(self, event_date: str, start_date: date, end_date: date) -> bool:
        """Check if event_date is within the given range"""
        try:
            # Parse the event date
            event_date_obj = parse(event_date, fuzzy=True)
            
            # Compare with start and end dates
            return start_date <= event_date_obj.date() <= end_date
        except Exception as e:
            # If there's an error in parsing, exclude the event to be safe
            logger.warning(f"Could not parse date '{event_date}': {e}")
            return False
    def _get_chrome_options_and_service(self):
        """Get Chrome options and service based on the current platform"""
        import platform
        import shutil
        import os
        
        chrome_options = Options()
        
        # Detect the platform
        system = platform.system().lower()
        logger.info(f"Detected platform: {system}")
        
        if system == "linux":
            # Linux/Debian environment (Streamlit Cloud)
            logger.info("Configuring Chrome for Linux/Debian environment")
            
            # Essential options for headless Chrome in Linux containers
            chrome_options.add_argument("--headless=new")  # Use new headless mode
            chrome_options.add_argument("--no-sandbox")  # Critical for containerized environments
            chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
            chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Memory and process management for limited resources
            chrome_options.add_argument("--memory-pressure-off")
            chrome_options.add_argument("--max_old_space_size=4096")
            chrome_options.add_argument("--single-process")  # Use single process mode
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            
            # Additional options for better compatibility
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--disable-setuid-sandbox")
            chrome_options.add_argument("--disable-software-rasterizer")
            
            # Set display for xvfb (matches packages.txt)
            if 'DISPLAY' not in os.environ:
                os.environ['DISPLAY'] = ':99'
                logger.info("Set DISPLAY environment variable for xvfb")
            
            # Try to use system Chrome/Chromium first (matching packages.txt)
            chrome_path = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
            chromedriver_path = shutil.which("chromium-driver") or shutil.which("chromedriver")
            
            if chrome_path:
                logger.info(f"Using system Chrome/Chromium at: {chrome_path}")
                chrome_options.binary_location = chrome_path
            else:
                logger.info("No system Chrome found, using default")
            
            # Determine which service to use
            if chromedriver_path:
                logger.info(f"Using system chromedriver at: {chromedriver_path}")
                service = Service(chromedriver_path)
            else:
                logger.info("System chromedriver not found, using ChromeDriverManager")
                service = Service(ChromeDriverManager().install())
        
        elif system == "darwin":
            # macOS environment
            logger.info("Configuring Chrome for macOS environment")
            
            # Basic options for macOS
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Use ChromeDriverManager for automatic driver management
            logger.info("Using ChromeDriverManager for macOS")
            service = Service(ChromeDriverManager().install())
        
        elif system == "windows":
            # Windows environment
            logger.info("Configuring Chrome for Windows environment")
            
            # Basic options for Windows
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Use ChromeDriverManager for automatic driver management
            logger.info("Using ChromeDriverManager for Windows")
            service = Service(ChromeDriverManager().install())
        
        else:
            # Unknown system - use safe defaults
            logger.warning(f"Unknown platform: {system}. Using safe default configuration.")
            
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Use ChromeDriverManager as fallback
            service = Service(ChromeDriverManager().install())
        
        return chrome_options, service
    
    def _scrape_events_from_url(self, url: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Scrape events from a specified URL within the date range"""
        
        # Get platform-specific Chrome configuration
        chrome_options, service = self._get_chrome_options_and_service()
        
        # Initialize the driver
        driver = None
        try:
            logger.info("Initializing Chrome driver...")
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info(f"Successfully initialized Chrome driver, loading: {url}")
            
            # Load the page
            driver.get(url)
            logger.info("Page loaded successfully")
            
            # Wait for events to load with better error handling
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "lw_cal_event"))
                )
                logger.info("Events container found")
            except TimeoutException:
                logger.warning("Timeout waiting for events to load")
                # Check if page loaded at all
                page_title = driver.title
                logger.info(f"Page title: {page_title}")
                # Return empty list instead of failing
                return []
            
            # Add a small delay
            time.sleep(2)
            
            # Find event elements with error checking
            event_elements = driver.find_elements(By.CLASS_NAME, "lw_cal_event")
            
            # DEBUG: Check if event_elements is None
            if event_elements is None:
                logger.error("event_elements is None - this shouldn't happen with Selenium")
                return []
            
            logger.info(f"Found {len(event_elements)} event elements")
            
            # If no events found, check page content
            if len(event_elements) == 0:
                logger.warning("No events found on page")
                # Debug: check page source
                page_source = driver.page_source
                logger.info(f"Page source length: {len(page_source) if page_source else 'None'}")
                if page_source and "lw_cal_event" in page_source:
                    logger.warning("Events exist in source but not found by selector")
                return []
            
            # Process events with better error handling
            event_data = []
            
            for i, element in enumerate(event_elements):
                try:
                    logger.info(f"Processing event {i+1}/{len(event_elements)}")
                    
                    # Extract event details with None checks
                    title_elements = element.find_elements(By.CSS_SELECTOR, "h4 a")
                    if not title_elements:
                        logger.warning(f"No title found for event {i+1}")
                        continue
                    
                    title_element = title_elements[0]
                    event_name = title_element.text
                    event_link = title_element.get_attribute("href")
                    
                    if not event_name:
                        logger.warning(f"Empty event name for event {i+1}")
                        continue
                    
                    # Get date/time with None check
                    date_time_elements = element.find_elements(By.CLASS_NAME, "date-time")
                    if date_time_elements:
                        date_time = date_time_elements[0].text
                        if date_time:  # Check if not None/empty
                            event_date = date_time.split("·")[0].strip() if "·" in date_time else date_time
                            event_time = date_time.split("·")[1].strip() if "·" in date_time else ""
                        else:
                            logger.warning(f"Empty date_time for event: {event_name}")
                            event_date = ""
                            event_time = ""
                    else:
                        logger.warning(f"No date-time element for event: {event_name}")
                        event_date = ""
                        event_time = ""
                    
                    # Check if event is within date range
                    if event_date and not self._is_within_date_range(event_date, start_date, end_date):
                        logger.info(f"Event outside date range: {event_name}")
                        continue
                    
                    # Get location with None check
                    location_elements = element.find_elements(By.CLASS_NAME, "map-marker")
                    location = location_elements[0].text if location_elements and location_elements[0].text else ""
                    
                    # Create event object
                    event = {
                        "event_name": event_name,
                        "event_link": event_link or "",
                        "event_date": event_date,
                        "event_time": event_time,
                        "event_location": location,
                        "event_facilitators": "",
                        "event_registration_link": "",
                        "event_description": ""
                    }
                    
                    event_data.append(event)
                    logger.info(f"Successfully processed: {event_name}")
                    
                except (StaleElementReferenceException, NoSuchElementException) as e:
                    logger.warning(f"Element error for event {i+1}: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error processing event {i+1}: {str(e)}")
                    continue
            
            logger.info(f"Successfully processed {len(event_data)} events")
            
            # Get additional details for each event
            for i, event in enumerate(event_data):
                try:
                    logger.info(f"Getting details for event {i+1}/{len(event_data)}: {event['event_name']}")
                    event_data[i] = self._get_event_details(driver, event)
                except Exception as e:
                    logger.warning(f"Error getting details for {event['event_name']}: {str(e)}")
                    # Continue with basic event data
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error in _scrape_events_from_url: {str(e)}")
            raise Exception(f"Failed to scrape events: {str(e)}")
            
        finally:
            # Always close the driver
            if driver:
                try:
                    driver.quit()
                    logger.info("Chrome driver closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing driver: {e}")
    def _get_event_details(self, driver, event: Dict[str, Any]) -> Dict[str, Any]:
        """Visit the event detail page and extract additional information"""
        try:
            # Navigate to the event detail page
            event_link = event.get("event_link", "")
            if not event_link:
                logger.warning("No event link provided")
                return event
                
            logger.info(f"Navigating to: {event_link}")
            driver.get(event_link)
            
            # Wait for the page to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Add a small delay
            time.sleep(1)
            
            # Get registration link if available
            try:
                reg_elements = driver.find_elements(By.CLASS_NAME, "lw_join_online")
                if reg_elements:
                    reg_element = reg_elements[0]
                    reg_link = reg_element.get_attribute("href")
                    if reg_link:
                        event["event_registration_link"] = reg_link
            except Exception as e:
                logger.warning(f"Error getting registration link: {e}")
            
            # Method 1: Try to get from the intro div
            try:
                intro_elements = driver.find_elements(By.CLASS_NAME, "intro")
                if intro_elements:
                    intro_div = intro_elements[0]
                    intro_text = intro_div.text
                    
                    if intro_text:  # Check if not None/empty
                        # Parse facilitator
                        facilitator_match = re.search(r'Facilitator[s]?:\s*(.*?)(?:\s*Description:|$)', intro_text, re.DOTALL)
                        if facilitator_match:
                            event["event_facilitators"] = facilitator_match.group(1).strip()
                        
                        # Parse description (from intro)
                        description_match = re.search(r'Description:\s*(.*?)$', intro_text, re.DOTALL)
                        if description_match:
                            event["event_description"] = description_match.group(1).strip()
            except Exception as e:
                logger.warning(f"Error parsing intro div: {e}")
            
            # Method 2: Try to get description from lw_calendar_event_description
            if not event.get("event_description"):
                try:
                    desc_elements = driver.find_elements(By.CLASS_NAME, "lw_calendar_event_description")
                    if desc_elements:
                        description_div = desc_elements[0]
                        desc_text = description_div.text
                        if desc_text:  # Check if not None/empty
                            event["event_description"] = desc_text.strip()
                except Exception as e:
                    logger.warning(f"Error getting description: {e}")
            
            # Method 3: If facilitator is still empty, try alternative parsing
            if not event.get("event_facilitators"):
                try:
                    body_element = driver.find_element(By.TAG_NAME, "body")
                    page_content = body_element.text if body_element else ""
                    
                    if page_content:  # Check if not None/empty
                        # Look for typical facilitator patterns
                        facilitator_patterns = [
                            r'Facilitator[s]?:\s*(.*?)(?:\n|Description:)',
                            r'Presenter[s]?:\s*(.*?)(?:\n|Description:)',
                            r'Instructor[s]?:\s*(.*?)(?:\n|Description:)'
                        ]
                        
                        for pattern in facilitator_patterns:
                            match = re.search(pattern, page_content, re.DOTALL)
                            if match:
                                event["event_facilitators"] = match.group(1).strip()
                                break
                except Exception as e:
                    logger.warning(f"Error in alternative facilitator parsing: {e}")
                    
        except Exception as e:
            logger.warning(f"Error getting details for {event.get('event_name', 'unknown')}: {str(e)}")
        
        return event