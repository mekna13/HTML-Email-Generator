# app/utils/event_validator.py
import re
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

logger = logging.getLogger("tamu_newsletter")

class EventValidator:
    """Utility class for validating event data quality"""
    
    def __init__(self):
        """Initialize the event validator"""
        # Common patterns for validation
        self.url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def validate_events_data(self, events_data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate complete events data structure
        
        Args:
            events_data: Dictionary containing events data
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Validate structure
        if not isinstance(events_data, dict):
            issues.append({
                "type": "structure",
                "severity": "critical",
                "message": "Events data must be a dictionary",
                "location": "root"
            })
            return False, issues
        
        # Check required keys
        required_keys = ["date_range", "cte_events", "elp_events"]
        for key in required_keys:
            if key not in events_data:
                issues.append({
                    "type": "structure",
                    "severity": "critical",
                    "message": f"Missing required key: {key}",
                    "location": "root"
                })
        
        # Validate date range
        if "date_range" in events_data:
            date_issues = self._validate_date_range(events_data["date_range"])
            issues.extend(date_issues)
        
        # Validate CTE events
        if "cte_events" in events_data:
            cte_issues = self._validate_event_list(events_data["cte_events"], "CTE")
            issues.extend(cte_issues)
        
        # Validate ELP events
        if "elp_events" in events_data:
            elp_issues = self._validate_event_list(events_data["elp_events"], "ELP")
            issues.extend(elp_issues)
        
        # Check if any critical issues exist
        critical_issues = [issue for issue in issues if issue["severity"] == "critical"]
        is_valid = len(critical_issues) == 0
        
        return is_valid, issues
    
    def _validate_date_range(self, date_range: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate date range structure and values"""
        issues = []
        
        if not isinstance(date_range, dict):
            issues.append({
                "type": "date_range",
                "severity": "critical",
                "message": "Date range must be a dictionary",
                "location": "date_range"
            })
            return issues
        
        # Check required date fields
        for field in ["start_date", "end_date"]:
            if field not in date_range:
                issues.append({
                    "type": "date_range",
                    "severity": "critical",
                    "message": f"Missing {field}",
                    "location": f"date_range.{field}"
                })
            else:
                # Try to parse the date
                try:
                    datetime.strptime(date_range[field], '%Y-%m-%d')
                except ValueError:
                    issues.append({
                        "type": "date_range",
                        "severity": "warning",
                        "message": f"Invalid date format for {field}: {date_range[field]} (expected YYYY-MM-DD)",
                        "location": f"date_range.{field}"
                    })
        
        # Check if start_date is before end_date
        if "start_date" in date_range and "end_date" in date_range:
            try:
                start = datetime.strptime(date_range["start_date"], '%Y-%m-%d')
                end = datetime.strptime(date_range["end_date"], '%Y-%m-%d')
                if start > end:
                    issues.append({
                        "type": "date_range",
                        "severity": "warning",
                        "message": "Start date is after end date",
                        "location": "date_range"
                    })
            except ValueError:
                pass  # Date format errors already caught above
        
        return issues
    
    def _validate_event_list(self, events: List[Dict[str, Any]], event_type: str) -> List[Dict[str, Any]]:
        """Validate a list of events"""
        issues = []
        
        if not isinstance(events, list):
            issues.append({
                "type": "event_list",
                "severity": "critical",
                "message": f"{event_type} events must be a list",
                "location": f"{event_type.lower()}_events"
            })
            return issues
        
        for i, event in enumerate(events):
            event_issues = self._validate_single_event(event, event_type, i)
            issues.extend(event_issues)
        
        return issues
    
    def _validate_single_event(self, event: Dict[str, Any], event_type: str, index: int) -> List[Dict[str, Any]]:
        """Validate a single event"""
        issues = []
        location_prefix = f"{event_type.lower()}_events[{index}]"
        
        if not isinstance(event, dict):
            issues.append({
                "type": "event",
                "severity": "critical",
                "message": "Event must be a dictionary",
                "location": location_prefix
            })
            return issues
        
        # CRITICAL required fields (must be present and not empty)
        critical_fields = {
            "event_name": "Event name",
            "event_link": "Event link", 
            "event_date": "Event date",
            "event_time": "Event time",
            "event_location": "Event location"
        }
        
        # Check critical fields
        for field, display_name in critical_fields.items():
            if field not in event:
                issues.append({
                    "type": "event",
                    "severity": "critical",
                    "message": f"Missing required field: {display_name}",
                    "location": f"{location_prefix}.{field}"
                })
            else:
                value = event.get(field, "")
                if not value or (isinstance(value, str) and not value.strip()):
                    issues.append({
                        "type": "event",
                        "severity": "critical",
                        "message": f"{display_name} cannot be empty",
                        "location": f"{location_prefix}.{field}"
                    })
        
        # OPTIONAL fields (can be missing entirely - only validate if present)
        optional_fields = {
            "event_facilitators": "Event facilitators",
            "event_registration_link": "Registration link", 
            "event_description": "Event description"
        }
        
        # Only validate optional fields if they exist
        for field, display_name in optional_fields.items():
            if field in event:
                value = event.get(field, "")
                # Only warn if field exists but is empty (not if completely absent)
                if isinstance(value, str) and not value.strip():
                    issues.append({
                        "type": "event",
                        "severity": "info",
                        "message": f"{display_name} is empty (consider removing field if no data available)",
                        "location": f"{location_prefix}.{field}"
                    })
        
        # Validate event name length (only if it exists)
        event_name = event.get("event_name", "")
        if event_name and len(event_name.strip()) < 5:
            issues.append({
                "type": "event",
                "severity": "warning",
                "message": "Event name is very short (less than 5 characters)",
                "location": f"{location_prefix}.event_name"
            })
        
        # Validate URLs (only if fields exist)
        for url_field in ["event_link", "event_registration_link"]:
            if url_field in event:
                url = event.get(url_field, "")
                if url and not self._is_valid_url(url):
                    issues.append({
                        "type": "event",
                        "severity": "warning",
                        "message": f"Invalid URL format for {url_field}",
                        "location": f"{location_prefix}.{url_field}"
                    })
        
        # Check for very short descriptions (only if field exists)
        if "event_description" in event:
            description = event.get("event_description", "")
            if description and len(description.strip()) < 20:
                issues.append({
                    "type": "event",
                    "severity": "info",
                    "message": "Event description is very short (less than 20 characters)",
                    "location": f"{location_prefix}.event_description"
                })
        
        # Validate date format (basic check)
        event_date = event.get("event_date", "")
        if event_date and not self._is_reasonable_date_format(event_date):
            issues.append({
                "type": "event",
                "severity": "info",
                "message": "Event date format may be unusual",
                "location": f"{location_prefix}.event_date"
            })
        
        # Validate time format (basic check)
        event_time = event.get("event_time", "")
        if event_time and not self._is_reasonable_time_format(event_time):
            issues.append({
                "type": "event",
                "severity": "info",
                "message": "Event time format may be unusual",
                "location": f"{location_prefix}.event_time"
            })
        
        return issues
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        if not url:
            return True  # Empty URLs are allowed
        return bool(self.url_pattern.match(url))
    
    def _is_reasonable_date_format(self, date_str: str) -> bool:
        """Check if date string looks reasonable"""
        if not date_str:
            return True
        
        # Check for common date patterns
        date_patterns = [
            r'\w+,\s+\w+\s+\d{1,2},\s+\d{4}',  # Monday, June 9, 2025
            r'\d{4}-\d{2}-\d{2}',  # 2025-06-09
            r'\d{1,2}/\d{1,2}/\d{4}',  # 6/9/2025
            r'\w+\s+\d{1,2},\s+\d{4}',  # June 9, 2025
        ]
        
        return any(re.search(pattern, date_str) for pattern in date_patterns)
    
    def _is_reasonable_time_format(self, time_str: str) -> bool:
        """Check if time string looks reasonable"""
        if not time_str:
            return True
        
        # Check for common time patterns
        time_patterns = [
            r'\d{1,2}:\d{2}[ap]m',  # 10:00am
            r'\d{1,2}:\d{2}\s*[AP]M',  # 10:00 AM
            r'\d{1,2}:\d{2}[ap]m\s*-\s*\d{1,2}:\d{2}[ap]m',  # 10:00am - 11:00am
            r'\d{1,2}:\d{2}\s*[AP]M\s*CDT',  # 10:00 AM CDT
        ]
        
        return any(re.search(pattern, time_str) for pattern in time_patterns)
    
    def get_validation_summary(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get a summary of validation issues"""
        summary = {
            "total_issues": len(issues),
            "critical": len([i for i in issues if i["severity"] == "critical"]),
            "warning": len([i for i in issues if i["severity"] == "warning"]),
            "info": len([i for i in issues if i["severity"] == "info"]),
            "by_type": {},
            "by_location": {}
        }
        
        # Group by type
        for issue in issues:
            issue_type = issue["type"]
            if issue_type not in summary["by_type"]:
                summary["by_type"][issue_type] = 0
            summary["by_type"][issue_type] += 1
        
        # Group by location (simplified)
        for issue in issues:
            location = issue["location"].split(".")[0]  # Get top-level location
            if location not in summary["by_location"]:
                summary["by_location"][location] = 0
            summary["by_location"][location] += 1
        
        return summary