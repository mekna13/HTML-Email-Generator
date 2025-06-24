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
        except:
            # If there's an error in parsing, include the event to be safe
            logger.warning(f"Could not parse date '{event_date}', including event anyway")
            return False
    
    def _scrape_events_from_url(self, url: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Scrape events from a specified URL within the date range"""
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize the driver with automatic ChromeDriver installation
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        try:
            # Load the page
            driver.get(url)
            
            # Wait for events to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "lw_cal_event"))
            )
            
            # Optional: Add a small delay to ensure everything is fully loaded
            time.sleep(2)
            
            # First, collect all basic information and URLs
            event_data = []
            event_elements = driver.find_elements(By.CLASS_NAME, "lw_cal_event")
            
            for element in event_elements:
                try:
                    # Extract event details
                    title_element = element.find_element(By.CSS_SELECTOR, "h4 a")
                    event_name = title_element.text
                    event_link = title_element.get_attribute("href")
                    
                    # Get other details
                    date_time = element.find_element(By.CLASS_NAME, "date-time").text
                    event_date = date_time.split("·")[0].strip() if "·" in date_time else date_time
                    event_time = date_time.split("·")[1].strip() if "·" in date_time else ""
                    
                    # Check if the event is within the specified date range
                    if not self._is_within_date_range(event_date, start_date, end_date):
                        continue  # Skip events outside the date range
                    
                    try:
                        location = element.find_element(By.CLASS_NAME, "map-marker").text
                    except (NoSuchElementException, StaleElementReferenceException):
                        location = ""
                    
                    # Create event object with basic info
                    event = {
                        "event_name": event_name,
                        "event_link": event_link,
                        "event_date": event_date,
                        "event_time": event_time,
                        "event_location": location,
                        "event_facilitators": "",
                        "event_registration_link": "",
                        "event_description": ""
                    }
                    
                    event_data.append(event)
                except (StaleElementReferenceException, NoSuchElementException) as e:
                    logger.warning(f"Skipping event due to: {str(e)}")
                    continue
            
            # Now, visit each event page to get additional details
            for event in event_data:
                try:
                    # Visit the event detail page to get additional information
                    event = self._get_event_details(driver, event)
                    logger.info(f"Processed: {event['event_name']}")
                except Exception as e:
                    logger.warning(f"Error getting details for {event['event_name']}: {str(e)}")
            
            return event_data
            
        finally:
            # Always close the driver
            driver.quit()
    
    def _get_event_details(self, driver, event: Dict[str, Any]) -> Dict[str, Any]:
        """Visit the event detail page and extract additional information"""
        try:
            # Navigate to the event detail page
            driver.get(event["event_link"])
            
            # Wait for the page to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Optional: Add a small delay
            time.sleep(1)
            
            # Get registration link if available
            try:
                reg_element = driver.find_element(By.CLASS_NAME, "lw_join_online")
                event["event_registration_link"] = reg_element.get_attribute("href")
            except (NoSuchElementException, StaleElementReferenceException):
                # No registration link found
                pass
            
            # Method 1: Try to get from the intro div
            try:
                intro_div = driver.find_element(By.CLASS_NAME, "intro")
                intro_text = intro_div.text
                
                # Parse facilitator
                facilitator_match = re.search(r'Facilitator[s]?:\s*(.*?)(?:\s*Description:|$)', intro_text, re.DOTALL)
                if facilitator_match:
                    event["event_facilitators"] = facilitator_match.group(1).strip()
                
                # Parse description (from intro)
                description_match = re.search(r'Description:\s*(.*?)$', intro_text, re.DOTALL)
                if description_match:
                    event["event_description"] = description_match.group(1).strip()
                    
            except (NoSuchElementException, StaleElementReferenceException):
                # No intro div found
                pass
                
            # Method 2: Try to get description from lw_calendar_event_description
            if not event["event_description"]:
                try:
                    description_div = driver.find_element(By.CLASS_NAME, "lw_calendar_event_description")
                    event["event_description"] = description_div.text.strip()
                except (NoSuchElementException, StaleElementReferenceException):
                    # No description div found
                    pass
            
            # Method 3: If facilitator is still empty, try alternative parsing from intro or page content
            if not event["event_facilitators"]:
                try:
                    page_content = driver.find_element(By.TAG_NAME, "body").text
                    
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
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"Error getting details for {event['event_name']}: {str(e)}")
        
        return event