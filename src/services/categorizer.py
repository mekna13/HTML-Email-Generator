# app/services/categorizer.py
import json
import time
import logging
import os
from typing import Dict, List, Any, Optional, Tuple

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Get logger
logger = logging.getLogger("tamu_newsletter")

class EventCategorizer:
    """
    Service class to handle event categorization functionality
    """
    
    def __init__(self):
        """Initialize the event categorizer"""
        self.descriptions_file = "category_descriptions.json"
        self.categorization_cache_file = "categorization_cache.json"
        self.weekly_descriptions_file = "weekly_category_descriptions.json"
        self.weekly_categorization_cache_file = "weekly_categorization_cache.json"
    
    def categorize_events(self, api_key: str, model: str = "gpt-3.5-turbo", debug_mode: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Categorize events using LLM
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            debug_mode: Whether to run in debug mode (ignored now - always runs directly)
            
        Returns:
            Tuple of (success, categorized_events_data)
        """
        logger.info(f"Starting event categorization with model: {model}")
        
        # Set environment variables for the OpenAI API
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_MODEL"] = model
        
        # Always run directly now - no subprocess needed
        return self._categorize_direct(api_key, model)
    
    def _categorize_direct(self, api_key: str, model: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Run categorization directly with integrated functionality
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            
        Returns:
            Tuple of (success, categorized_events_data)
        """
        logger.info("Running categorization directly with integrated functionality")
        
        try:
            # Load event data
            logger.info("Loading events data...")
            data = self._load_events_data()
            if not data:
                raise Exception("Failed to load events data. Make sure events.json exists.")
            
            # Extract event lists and separate weekly events
            cte_events, cte_weekly_events = self._separate_weekly_events(data.get("cte_events", []))
            elp_events, elp_weekly_events = self._separate_weekly_events(data.get("elp_events", []))
            
            logger.info(f"Found {len(cte_events)} regular CTE events, {len(cte_weekly_events)} weekly CTE event groups")
            logger.info(f"Found {len(elp_events)} regular ELP events, {len(elp_weekly_events)} weekly ELP event groups")
            
            # Initialize LLM for categorization (very low temperature)
            logger.info("Initializing LLM for categorization...")
            categorization_llm = self._initialize_llm(api_key, model, temperature=0.1)
            if not categorization_llm:
                raise Exception("Failed to initialize LLM. Cannot proceed with categorization.")
            
            # Categorize regular events using LLM
            categorized_cte = self._categorize_events_with_llm(cte_events, "CTE", categorization_llm)
            categorized_elp = self._categorize_events_with_llm(elp_events, "ELP", categorization_llm)
            
            # Process weekly events
            weekly_events = self._process_weekly_events(cte_weekly_events + elp_weekly_events, categorization_llm)
            
            # Load existing descriptions
            stored_descriptions = self._load_category_descriptions()
            stored_weekly_descriptions = self._load_weekly_category_descriptions()
            
            logger.info(f"Loaded {len(stored_descriptions)} stored category descriptions")
            logger.info(f"Loaded {len(stored_weekly_descriptions)} stored weekly category descriptions")
            
            # Check if we need to generate any new descriptions
            new_categories = []
            new_weekly_categories = []
            
            for categories in [categorized_cte, categorized_elp]:
                for category in categories:
                    if category["category_name"] not in stored_descriptions:
                        new_categories.append((category["category_name"], category["events"]))
            
            for weekly_event in weekly_events:
                # Only generate descriptions for weekly events that don't have cached descriptions
                # and still have the events array (meaning they weren't loaded from cache)
                if (weekly_event["category_name"] not in stored_weekly_descriptions and 
                    "events" in weekly_event):
                    new_weekly_categories.append(weekly_event)
            
            logger.info(f"Found {len(new_categories)} new regular categories that need descriptions")
            logger.info(f"Found {len(new_weekly_categories)} new weekly categories that need descriptions")
            
            # Initialize LLM for descriptions (higher temperature for creative content)
            description_llm = None
            if new_categories or new_weekly_categories:
                logger.info("Initializing LLM for generating new descriptions...")
                description_llm = self._initialize_llm(api_key, model, temperature=0.7)
                if not description_llm:
                    logger.warning("Failed to initialize LLM for descriptions. Using placeholders.")
                
                # Generate descriptions for new regular categories
                for category_name, events in new_categories:
                    if description_llm:
                        description = self._generate_description_with_llm(category_name, events, description_llm)
                    else:
                        description = f"A series of events focused on {category_name}."
                    
                    stored_descriptions[category_name] = description
                    logger.info(f"Generated new description for: {category_name}")
                
                # Generate descriptions for new weekly categories
                for weekly_event in new_weekly_categories:
                    if description_llm:
                        description = self._generate_weekly_description_with_llm(weekly_event, description_llm)
                        weekly_info = self._generate_weekly_info_with_llm(weekly_event, description_llm)
                    else:
                        description = f"A weekly series of events focused on {weekly_event['category_name']}."
                        weekly_info = "Schedule and facilitator information to be determined."
                    
                    stored_weekly_descriptions[weekly_event["category_name"]] = {
                        "description": description,
                        "weekly_event_info": weekly_info
                    }
                    logger.info(f"Generated new weekly description for: {weekly_event['category_name']}")
                
                # Save updated descriptions
                self._save_category_descriptions(stored_descriptions)
                self._save_weekly_category_descriptions(stored_weekly_descriptions)
            
            # Apply descriptions to categorized events
            for category in categorized_cte + categorized_elp:
                category_name = category["category_name"]
                if category_name in stored_descriptions:
                    category["description"] = stored_descriptions[category_name]
                else:
                    category["description"] = f"Events related to {category_name}."
            
            # Apply descriptions to weekly events
            for weekly_event in weekly_events:
                category_name = weekly_event["category_name"]
                if category_name in stored_weekly_descriptions:
                    weekly_event["description"] = stored_weekly_descriptions[category_name]["description"]
                    weekly_event["weekly_event_info"] = stored_weekly_descriptions[category_name]["weekly_event_info"]
                else:
                    weekly_event["description"] = f"Weekly events related to {category_name}."
                    weekly_event["weekly_event_info"] = "Schedule and facilitator information to be determined."
                
                # Remove events array from final output (not needed in JSON structure)
                if "events" in weekly_event:
                    del weekly_event["events"]
            
            # Build new structure
            structured_data = {
                "date_range": data.get("date_range", {}),
                "cte_events": categorized_cte,
                "elp_events": categorized_elp,
                "weekly_events": weekly_events
            }
            
            # Save the categorized data
            output_path = "categorized_events.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(structured_data, f, indent=2)
            
            logger.info(f"Categorized events saved to {output_path}")
            
            return (True, structured_data)
            
        except Exception as e:
            logger.error(f"Error during categorization: {str(e)}")
            return (False, {"error": f"Error during categorization: {str(e)}"})
    
    def _separate_weekly_events(self, events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Separate weekly events from regular events
        
        Args:
            events: List of events
            
        Returns:
            Tuple of (regular_events, weekly_events_grouped)
        """
        regular_events = []
        weekly_events_raw = []
        
        for event in events:
            if event.get("event_time", "").find("Weekly") != -1:
                weekly_events_raw.append(event)
            else:
                regular_events.append(event)
        
        # Group weekly events by name
        weekly_groups = {}
        for event in weekly_events_raw:
            name = event["event_name"]
            if name not in weekly_groups:
                weekly_groups[name] = []
            weekly_groups[name].append(event)
        
        # Convert to list of grouped events
        weekly_events_grouped = []
        for name, group in weekly_groups.items():
            weekly_events_grouped.append({
                "category_name": name,
                "events": group,
                "event_link": group[0]["event_link"],  # Use first event's link
                "event_registration_link": group[0]["event_registration_link"]  # Use first event's registration
            })
        
        return regular_events, weekly_events_grouped
    
    def _process_weekly_events(self, weekly_event_groups: List[Dict[str, Any]], llm: ChatOpenAI) -> List[Dict[str, Any]]:
        """
        Process weekly events into the required structure with caching support
        
        Args:
            weekly_event_groups: List of weekly event groups
            llm: LLM instance for processing
            
        Returns:
            List of processed weekly events
        """
        processed_weekly_events = []
        
        # Load weekly categorization cache
        weekly_cache = self._load_weekly_categorization_cache()
        cache_updated = False
        
        for group in weekly_event_groups:
            # Create cache key based on event name and event instances
            cache_key = self._get_weekly_event_cache_key(group)
            
            # Check if this weekly event group is already cached
            if cache_key in weekly_cache:
                logger.info(f"Using cached weekly event: {group['category_name']}")
                cached_event = weekly_cache[cache_key].copy()
                # Remove the events array from cache data (not needed in final output)
                if "events" in cached_event:
                    del cached_event["events"]
                processed_weekly_events.append(cached_event)
            else:
                logger.info(f"Processing new weekly event: {group['category_name']}")
                processed_event = {
                    "category_name": group["category_name"],
                    "description": "",  # Will be filled later
                    "event_link": group["event_link"],
                    "event_registration_link": group["event_registration_link"],
                    "weekly_event_info": "",  # Will be filled later
                    "events": group["events"]  # Keep for description generation
                }
                processed_weekly_events.append(processed_event)
                
                # Cache this weekly event group for future use
                weekly_cache[cache_key] = processed_event.copy()
                cache_updated = True
        
        # Save updated cache if there were changes
        if cache_updated:
            self._save_weekly_categorization_cache(weekly_cache)
        
        return processed_weekly_events
    
    def _get_weekly_event_cache_key(self, weekly_group: Dict[str, Any]) -> str:
        """
        Generate a cache key for weekly events based on event name and instances
        
        Args:
            weekly_group: Weekly event group data
            
        Returns:
            Cache key string
        """
        # Use event name and count of instances as key
        event_name = weekly_group["category_name"]
        event_count = len(weekly_group["events"])
        
        # Include basic schedule info to detect changes
        days = set()
        times = set()
        for event in weekly_group["events"]:
            day = event.get("event_date", "").split(",")[0].strip()
            time = event.get("event_time", "").split(" Weekly")[0].strip()
            if day:
                days.add(day)
            if time:
                times.add(time)
        
        # Create a deterministic key
        schedule_hash = f"{len(days)}days_{len(times)}times"
        return f"{event_name}|{event_count}|{schedule_hash}"
    
    def _load_weekly_categorization_cache(self) -> Dict[str, Any]:
        """Load cached weekly categorization results"""
        if os.path.exists(self.weekly_categorization_cache_file):
            try:
                with open(self.weekly_categorization_cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading weekly categorization cache: {e}")
        return {}
    
    def _save_weekly_categorization_cache(self, cache: Dict[str, Any]) -> bool:
        """Save weekly categorization results to cache"""
        try:
            with open(self.weekly_categorization_cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving weekly categorization cache: {e}")
            return False
    
    def _generate_weekly_description_with_llm(self, weekly_event: Dict[str, Any], llm: ChatOpenAI) -> str:
        """
        Generate a description for a weekly event using LLM
        
        Args:
            weekly_event: Weekly event data
            llm: Initialized LangChain LLM
            
        Returns:
            Generated description
        """
        import time as time_module  # Import with alias to avoid conflicts
        
        template = """
        Create an engaging 4-line description for a weekly academic event series at Texas A&M University.
        
        Event Series: {category_name}
        
        Sample Event Description:
        {event_description}
        
        Write a compelling description that:
        - Explains what this weekly series is about
        - Highlights the value and benefits for attendees  
        - Encourages faculty and staff to sign up
        - Uses an enthusiastic, professional tone
        
        DO NOT include specific dates, times, locations, or facilitator names.
        Focus on the content and benefits of the series.
        Keep it to exactly 5 lines.
        
        Description:
        """
        
        # Use the first event's description as sample
        sample_description = weekly_event["events"][0].get("event_description", "")
        if len(sample_description) > 300:
            sample_description = sample_description[:300] + "..."
        
        prompt = ChatPromptTemplate.from_template(template)
        formatted_prompt = prompt.format(
            category_name=weekly_event["category_name"],
            event_description=sample_description
        )
        
        try:
            response = llm.invoke(formatted_prompt)
            description = response.content.strip()
            time_module.sleep(1)  # Rate limiting with explicit module reference
            return description
        except Exception as e:
            logger.error(f"Error generating weekly description: {e}")
            return f"A weekly series focused on {weekly_event['category_name']}."
    
    def _generate_weekly_info_with_llm(self, weekly_event: Dict[str, Any], llm: ChatOpenAI) -> str:
        """
        Generate weekly event info (schedule and facilitators) using LLM
        
        Args:
            weekly_event: Weekly event data
            llm: Initialized LangChain LLM
            
        Returns:
            Generated weekly info
        """
        import time as time_module  # Import with alias to avoid conflicts
        
        # Extract schedule and facilitator information
        events = weekly_event["events"]
        
        # Get unique days, times, and facilitators
        days_times = []
        facilitators = set()
        
        for event in events:
            day = event.get("event_date", "").split(",")[0].strip()
            event_time = event.get("event_time", "").split(" Weekly")[0].strip()
            location = event.get("event_location", "").strip()
            facilitator = event.get("event_facilitators", "").strip()
            
            if day and event_time:
                location_info = f" in {location}" if location and location != "Zoom" else " (Virtual)" if location == "Zoom" else ""
                days_times.append(f"{day}s at {event_time}{location_info}")
            
            if facilitator:
                facilitators.add(facilitator)
        
        template = """
        Create a concise weekly event information summary based on the following schedule and facilitator data:
        
        Event Series: {category_name}
        
        Schedule Information:
        {schedule_info}
        
        Facilitators:
        {facilitators_info}
        
        Write a brief, informative summary that:
        - Clearly states when the sessions take place
        - Lists the facilitators
        - Uses a professional, clear tone
        - Is 2-3 lines maximum
        
        Weekly Event Info:
        """
        
        schedule_text = "\n".join([f"- {dt}" for dt in days_times])
        facilitators_text = "\n".join([f"- {f}" for f in sorted(facilitators)])
        
        prompt = ChatPromptTemplate.from_template(template)
        formatted_prompt = prompt.format(
            category_name=weekly_event["category_name"],
            schedule_info=schedule_text,
            facilitators_info=facilitators_text
        )
        
        try:
            response = llm.invoke(formatted_prompt)
            weekly_info = response.content.strip()
            time_module.sleep(1)  # Rate limiting with explicit module reference
            return weekly_info
        except Exception as e:
            logger.error(f"Error generating weekly info: {e}")
            return "Schedule and facilitator information available upon registration."
    
    def _load_weekly_category_descriptions(self) -> Dict[str, Dict[str, str]]:
        """Load existing weekly category descriptions from JSON file"""
        if os.path.exists(self.weekly_descriptions_file):
            try:
                with open(self.weekly_descriptions_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading weekly category descriptions: {e}")
        return {}
    
    def _save_weekly_category_descriptions(self, descriptions: Dict[str, Dict[str, str]]) -> bool:
        """Save weekly category descriptions to JSON file"""
        try:
            with open(self.weekly_descriptions_file, "w", encoding="utf-8") as f:
                json.dump(descriptions, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving weekly category descriptions: {e}")
            return False
    
    # [Keep all the existing methods from the original categorizer.py]
    def _load_events_data(self, file_path: str = "events.json") -> Optional[Dict[str, Any]]:
        """Load events data from JSON file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Error loading events data: {e}")
            return None
    
    def _load_category_descriptions(self) -> Dict[str, str]:
        """Load existing category descriptions from JSON file"""
        if os.path.exists(self.descriptions_file):
            try:
                with open(self.descriptions_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading category descriptions: {e}")
        return {}
    
    def _save_category_descriptions(self, descriptions: Dict[str, str]) -> bool:
        """Save category descriptions to JSON file"""
        try:
            with open(self.descriptions_file, "w", encoding="utf-8") as f:
                json.dump(descriptions, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving category descriptions: {e}")
            return False
    
    def _load_categorization_cache(self) -> Dict[str, Any]:
        """Load cached categorization results"""
        if os.path.exists(self.categorization_cache_file):
            try:
                with open(self.categorization_cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading categorization cache: {e}")
        return {}
    
    def _save_categorization_cache(self, cache: Dict[str, Any]) -> bool:
        """Save categorization results to cache"""
        try:
            with open(self.categorization_cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving categorization cache: {e}")
            return False
    
    def _initialize_llm(self, api_key: str, model: str, temperature: float = 0.1) -> Optional[ChatOpenAI]:
        """Initialize the LangChain LLM"""
        try:
            llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key
            )
            return llm
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            return None
    
    def _get_event_hash(self, event: Dict[str, Any]) -> str:
        """Create a deterministic hash for an event based on its name and date"""
        event_name = event.get("event_name", "")
        event_date = event.get("event_date", "")
        return f"{event_name}|{event_date}"
    
    def _categorize_events_with_llm(self, events: List[Dict[str, Any]], event_type: str, llm: ChatOpenAI) -> List[Dict[str, Any]]:
        """
        Use LLM to categorize events in a deterministic way
        
        Args:
            events: List of event objects
            event_type: String indicating "cte" or "elp" events
            llm: Initialized LangChain LLM
            
        Returns:
            Categorized events structure
        """
        if not events or len(events) == 0:
            logger.info(f"No {event_type} events to categorize")
            return []
        
        # Check categorization cache first
        categorization_cache = self._load_categorization_cache()
        cache_key = f"{event_type}_categories"
        
        # Create mapping of event hashes for this batch
        event_hashes = {self._get_event_hash(event): i for i, event in enumerate(events)}
        
        # Check if cache exists and all current events are in it
        if (cache_key in categorization_cache and 
            all(self._get_event_hash(event) in categorization_cache.get(f"{event_type}_event_map", {}) 
                for event in events)):
            
            logger.info(f"Using cached categorization for {event_type} events")
            
            # Get cached categories
            cached_categories = categorization_cache[cache_key]
            event_map = categorization_cache[f"{event_type}_event_map"]
            
            # Build categories with actual event objects
            categorized_events = []
            for category in cached_categories:
                category_name = category["category_name"]
                category_obj = {
                    "category_name": category_name,
                    "description": "",  # Will be filled later
                    "events": []
                }
                
                # Add events to category
                for event_hash, cat_name in event_map.items():
                    if cat_name == category_name and event_hash in event_hashes:
                        event_idx = event_hashes[event_hash]
                        category_obj["events"].append(events[event_idx])
                
                # Only add category if it has events
                if category_obj["events"]:
                    categorized_events.append(category_obj)
            
            logger.info(f"Loaded {len(categorized_events)} categories from cache")
            for category in categorized_events:
                logger.info(f"  - {category['category_name']}: {len(category['events'])} events")
            
            return categorized_events
        
        logger.info(f"Categorizing {event_type} events with LLM...")
        
        # Format events for the prompt
        formatted_events = []
        for i, event in enumerate(events):
            # Extract relevant fields for categorization
            name = event.get("event_name", "")
            description = event.get("event_description", "")
            date = event.get("event_date", "")
            
            # Truncate description if too long
            if description and len(description) > 200:
                description = description[:200] + "..."
                
            formatted_events.append(f"Event {i}:\nName: {name}\nDate: {date}\nDescription: {description}\n")
        
        # Join formatted events into a string
        events_text = "\n".join(formatted_events)
        
        # Create prompt for deterministic categorization
        template = """
        You are an expert academic event organizer with years of experience. I need you to categorize university events into logical series or groups.

        CATEGORIZATION RULES:
        1. Events that are clearly part of the same series should be grouped together
        2. When titles follow patterns like "Series Name: Session X" or "Series Name (Part X)", group by the base series name
        3. For events with dates in titles like "Series (May 2025)", group by the base name without the date
        4. The goal is to create intuitive groupings that would make sense in a newsletter
        5. Create between 1-5 categories total, with clear names that describe the event type
        6. Every event must be assigned to exactly one category

        EXAMPLES:
        - "Workshop Series: Introduction" and "Workshop Series: Advanced Topics" -> both in "Workshop Series"
        - "ELP Practice Group For Instructors May 2025 (Session 1)" and "ELP Practice Group For Instructors May 2025 (Session 2)" -> both in "ELP Practice Group For Instructors"
        - Standalone events that don't fit elsewhere can go in "Additional Events"

        Here are the events to categorize:

        {events_text}

        Provide your categorization as a JSON object with the following format:
        1. A "categories" array containing objects with "category_name" and "description" (leave description blank)
        2. An "event_assignments" object mapping event indices to category names

        Example response format:
        {{
          "categories": [
            {{
              "category_name": "Workshop Series",
              "description": ""
            }},
            {{
              "category_name": "Faculty Training",
              "description": ""
            }}
          ],
          "event_assignments": {{
            "0": "Workshop Series",
            "1": "Workshop Series",
            "2": "Faculty Training",
            "3": "Faculty Training"
          }}
        }}

        Be sure every event (0 to {max_index}) is assigned to a category.
        Only output the JSON object, nothing else.
        """
        
        # Create and format prompt
        prompt = ChatPromptTemplate.from_template(template)
        formatted_prompt = prompt.format(
            events_text=events_text,
            max_index=len(events) - 1
        )
        
        # Get response from LLM
        try:
            response = llm.invoke(formatted_prompt)
            response_content = response.content.strip()
            
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in response_content:
                response_content = response_content.split("```json")[1].split("```")[0].strip()
            elif "```" in response_content:
                response_content = response_content.split("```")[1].split("```")[0].strip()
                
            # Parse JSON
            categorization = json.loads(response_content)
            
            # Get categories and event assignments
            categories = categorization.get("categories", [])
            event_assignments = categorization.get("event_assignments", {})
            
            # Create categorized events
            categorized_events = []
            category_map = {cat["category_name"]: {"category_name": cat["category_name"], "description": "", "events": []} 
                             for cat in categories}
            
            # Assign events to categories
            for event_idx, category_name in event_assignments.items():
                event_idx = int(event_idx)
                if 0 <= event_idx < len(events) and category_name in category_map:
                    category_map[category_name]["events"].append(events[event_idx])
            
            # Convert to list and filter empty categories
            categorized_events = [cat for cat in category_map.values() if cat["events"]]
            
            # Update cache
            event_map = {}
            for event_idx, category_name in event_assignments.items():
                event_idx = int(event_idx)
                if 0 <= event_idx < len(events):
                    event_hash = self._get_event_hash(events[event_idx])
                    event_map[event_hash] = category_name
            
            categorization_cache[cache_key] = categories
            categorization_cache[f"{event_type}_event_map"] = event_map
            self._save_categorization_cache(categorization_cache)
            
            # Sort categories by number of events (descending)
            categorized_events.sort(key=lambda x: len(x["events"]), reverse=True)
            
            logger.info(f"Created {len(categorized_events)} categories for {event_type} events")
            for category in categorized_events:
                logger.info(f"  - {category['category_name']}: {len(category['events'])} events")
            
            return categorized_events
        
        except Exception as e:
            logger.error(f"Error in LLM categorization: {e}")
            logger.info("Falling back to basic categorization")
            
            # Simple fallback categorization
            category_obj = {
                "category_name": f"{event_type} Events",
                "description": "",
                "events": events.copy()
            }
            
            return [category_obj]
    
    def _generate_description_with_llm(self, category_name: str, events: List[Dict[str, Any]], llm: ChatOpenAI) -> str:
        """
        Generate a description for a category using LLM
        
        Args:
            category_name: Name of the category
            events: List of events in this category
            llm: Initialized LangChain LLM
            
        Returns:
            Generated description
        """
        # Create prompt template for description generation
        template = """
        Create an engaging 3-4 line description for a category of academic events at Texas A&M University.
        
        Category: {category_name}
        
        Events in this category:
        {event_descriptions}
        
        Write a compelling description that:
        - Explains what this category/series of events is about
        - Highlights the value and benefits for attendees
        - Encourages faculty and staff to sign up
        - Uses an enthusiastic, professional tone
        
        DO NOT include specific dates, times, locations, or facilitator names.
        DO NOT exceed 4 lines of text.
        
        Description:
        """
        
        # Format event descriptions for context
        event_texts = []
        for event in events[:3]:  # Limit to first 3 events to keep prompt reasonable
            name = event.get("event_name", "")
            desc = event.get("event_description", "")
            
            # Truncate description if too long
            if desc and len(desc) > 200:
                desc = desc[:200] + "..."
                
            event_texts.append(f"- {name}\n  {desc}")
        
        event_descriptions = "\n\n".join(event_texts)
        
        # Create and format prompt
        prompt = ChatPromptTemplate.from_template(template)
        formatted_prompt = prompt.format(
            category_name=category_name,
            event_descriptions=event_descriptions
        )
        
        # Get response from LLM
        try:
            response = llm.invoke(formatted_prompt)
            description = response.content.strip()
            
            # Add some delay to avoid rate limits
            time.sleep(1)
            
            return description
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return f"A series of events focused on {category_name}."