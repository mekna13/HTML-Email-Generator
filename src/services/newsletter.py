# app/services/newsletter.py
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

# Get logger
logger = logging.getLogger("tamu_newsletter")

class NewsletterGenerator:
    """
    Service class to handle newsletter generation functionality
    """
    
    def __init__(self):
        """Initialize the newsletter generator"""
        self.categorized_events_path = "categorized_events.json"
        self.categorization_cache_path = "categorization_cache.json"
        self.newsletter_output_path = "newsletter.html"
    
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
            
        if not os.path.exists(self.categorization_cache_path):
            error_msg = f"Categorization cache file not found: {self.categorization_cache_path}"
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
            # Generate HTML content
            logger.info("Generating HTML content")
            html_content = self._generate_email_html(
                self.categorized_events_path, 
                self.categorization_cache_path
            )
            
            # Save the newsletter to file
            with open(self.newsletter_output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            logger.info(f"Newsletter saved to {self.newsletter_output_path}")
            
            return (True, html_content)
            
        except Exception as e:
            logger.error(f"Error during newsletter generation: {str(e)}")
            return (False, f"Error during newsletter generation: {str(e)}")
    
    def _generate_email_html(self, categorized_events_path: str, categorization_cache_path: str) -> str:
        """Generate the complete HTML newsletter"""
        # Load the JSON data
        with open(categorized_events_path, 'r') as f:
            categorized_events = json.load(f)
        
        with open(categorization_cache_path, 'r') as f:
            categorization_cache = json.load(f)
        
        # Extract date range
        date_range = categorized_events.get('date_range', {})
        
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
                                                <img width="600" height="100" style="width:6.25in;height:1.0416in" src="https://mail.google.com/mail/u/0?ui=2&amp;ik=612bb719ee&amp;attid=0.7&amp;permmsgid=msg-f:1824508954730130781&amp;th=1951f53a48356d5d&amp;view=fimg&amp;fur=ip&amp;permmsgid=msg-f:1824508954730130781&amp;sz=s0-l75-ft&amp;attbid=ANGjdJ-G1dcgArBtOb511i9bAHOEDifQXjZeE9MIGC8iM9EkfAKTkWiX-RFADpzBw22MfSMgsqjR1_LhHu4ICNFtQ4bblSCBqoSkFVna2uzIhZNUqiql-SRUNP9EZso&amp;disp=emb&amp;zw" alt="square texas a and m logo on an off white marble background with words texas a and m university center for teaching excellence">
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
        
        # Add CTE event categories
        if 'cte_events' in categorized_events:
            for category in categorized_events['cte_events']:
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
        
        # Add ELP banner before ELP events
        html += """
                            <table border="0" cellspacing="0" cellpadding="0" width="600" style="width:6.25in;color:inherit;font-size:inherit">
                                <tbody>
                                    <tr>
                                        <td style="padding:0in 0in 0in 0in">
                                            <p class="MsoNormal" align="center" style="text-align:center">
                                                <img border="0" width="600" height="191" style="width:6.25in;height:1.9895in" src="https://mail.google.com/mail/u/0?ui=2&amp;ik=612bb719ee&amp;attid=0.5&amp;permmsgid=msg-f:1824508954730130781&amp;th=1951f53a48356d5d&amp;view=fimg&amp;fur=ip&amp;permmsgid=msg-f:1824508954730130781&amp;sz=s0-l75-ft&amp;attbid=ANGjdJ_Txvoygmr-RLadzYzqS0eCWVegefXS1_KdjNlRfNELgh95QwjYY0RJUeKJ2RqOfphfvK1uV4cgqVWKRdQuuyeEyTRCvTTVswf_gt7AHcso7RWpiuXkDpC76Dk&amp;disp=emb&amp;zw" alt="image of two students studying outdoors with English language proficiency workshops superimposed in a maroon bar">
                                            </p>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
        """
        
        # Add ELP event categories
        if 'elp_events' in categorized_events:
            for category in categorized_events['elp_events']:
                category_name = category.get('category_name', '')
                category_description = category.get('description', '')
                events = category.get('events', [])
                
                # Add category title and description
                html += self._category_template(category_name, category_description)
                
                # Add each event in the category
                for event in events:
                    html += self._event_template(event)
                
                # Add separator after category (except for the last one)
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
                                                    <a href="https://ecomms.marcomm.tamu.edu/trk/click?ref=z177i6rteh_0-114_0x38e3x0314" target="_blank"><span style="text-decoration:none"><img border="0" width="40" height="40" style="width:.4166in;height:.4166in" src="https://mail.google.com/mail/u/0?ui=2&amp;ik=612bb719ee&amp;attid=0.13&amp;permmsgid=msg-f:1824508954730130781&amp;th=1951f53a48356d5d&amp;view=fimg&amp;fur=ip&amp;permmsgid=msg-f:1824508954730130781&amp;sz=s0-l75-ft&amp;attbid=ANGjdJ_s0rgiJeLwnyaRRC4CXu0ovfZXjGEzTjUc5J4TQ9t6OVp30XuGX3cXiPxxz9KuDWOZRO5NW71ZMANDMJ3imgimwUPh7oOxS2gy3Kx-XhwwTSntq4Sq8xQyYcY&amp;disp=emb&amp;zw"></span></a><u></u><u></u>
                                                </p>
                                            </td>
                                            <td width="75" style="width:56.25pt;padding:0in 0in 0in 0in">
                                                <p class="MsoNormal" align="center" style="text-align:center">
                                                    <a href="https://ecomms.marcomm.tamu.edu/trk/click?ref=z177i6rteh_0-114_0x38e4x0314" target="_blank"><span style="text-decoration:none"><img border="0" width="40" height="40" style="width:.4166in;height:.4166in" src="https://mail.google.com/mail/u/0?ui=2&amp;ik=612bb719ee&amp;attid=0.3&amp;permmsgid=msg-f:1824508954730130781&amp;th=1951f53a48356d5d&amp;view=fimg&amp;fur=ip&amp;permmsgid=msg-f:1824508954730130781&amp;sz=s0-l75-ft&amp;attbid=ANGjdJ9z9grEwlHVlbh3t3nKs_qewPUo7aXyNwMxzUP4KXUFHhx9J8FNY1m7lKvo4tJ2Ot4JARprZW7Pb32EDDhpf2lz2XYNO2DA_cp5ZLTQQ8pEDqScoSKRTFC8Q94&amp;disp=emb&amp;zw" alt="Email Icon"></span></a><u></u><u></u>
                                                </p>
                                            </td>
                                            <td width="75" style="width:56.25pt;padding:0in 0in 0in 0in">
                                                <p class="MsoNormal" align="center" style="text-align:center">
                                                    <a href="https://ecomms.marcomm.tamu.edu/trk/click?ref=z177i6rteh_0-114_0x38e5x0314" target="_blank"><span style="text-decoration:none"><img border="0" width="40" height="40" style="width:.4166in;height:.4166in" src="https://mail.google.com/mail/u/0?ui=2&amp;ik=612bb719ee&amp;attid=0.11&amp;permmsgid=msg-f:1824508954730130781&amp;th=1951f53a48356d5d&amp;view=fimg&amp;fur=ip&amp;permmsgid=msg-f:1824508954730130781&amp;sz=s0-l75-ft&amp;attbid=ANGjdJ_-LPekFNswb7_3C4FS-GB0fttYlt8A4-obh1RJ--EfOLhjJJQkxpj21TjiDhHEzbU7I11I_CzJdBGzETxflc6R_zu4j7MRxsTWx4McMNBvEoCKFezHIq2kzq0&amp;disp=emb&amp;zw"></span></a><u></u><u></u>
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
    
    def _category_template(self, category_name: str, category_description: str) -> str:
        """Generate HTML for category title and description"""
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
        """Generate HTML for an individual event"""
        # Extract event details
        event_name = event.get('event_name', '')
        event_link = event.get('event_link', '')
        event_date = event.get('event_date', '')
        event_time = event.get('event_time', '')
        event_location = event.get('event_location', '')
        event_facilitators = event.get('event_facilitators', '')
        event_description = event.get('event_description', '')
        
        # Shorten the description for the newsletter
        if len(event_description) > 150:
            short_description = event_description[:150] + "..."
        else:
            short_description = event_description
        
        event_registration_link = event.get('event_registration_link', '')
        
        # Convert event title to uppercase
        event_name_uppercase = event_name.upper()
        
        # Generate a short calendar icon string based on the date
        calendar_icon_alt = event_date.split(',')[0].strip() if ',' in event_date else event_date
        
        # Short version of event name for links (but keep original case for readability)
        event_name_short = event_name[:40] + '...' if len(event_name) > 40 else event_name
        
        return f"""
                            <div align="center">
                                <table border="0" cellspacing="0" cellpadding="0" width="600" style="width:6.25in;color:inherit;font-size:inherit">
                                    <tbody>
                                        <tr>
                                            <td width="45" valign="top" style="width:33.75pt;padding:3.75pt 3.75pt 0in 0in">
                                                <p class="MsoNormal" align="center" style="text-align:center">
                                                    <img border="0" width="41" height="43" style="width:.427in;height:.4479in" src="https://mail.google.com/mail/u/0?ui=2&amp;ik=612bb719ee&amp;attid=0.15&amp;permmsgid=msg-f:1824508954730130781&amp;th=1951f53a48356d5d&amp;view=fimg&amp;fur=ip&amp;permmsgid=msg-f:1824508954730130781&amp;sz=s0-l75-ft&amp;attbid=ANGjdJ9YQnX5549G3FvZaV0ZWIqPntjrIaEqt7xwfQhlLkMQ9gBFaRsc_-3RZZ3pwfaUtSL-9kLEb1YuhYqxt7a9t2-8IwaRoIh7SQV0fbaJg5I1T-3o_DUK926M--Y&amp;disp=emb&amp;zw" alt="calendar representation of {calendar_icon_alt}"><u></u><u></u>
                                                </p>
                                            </td>
                                            <td valign="top" style="padding:0in 0in 11.25pt 0in">
                                                <p class="MsoNormal">
                                                    <b><a href="{event_link}" style="text-decoration:underline;color:#500000" target="_blank"><span style="font-size:9.0pt;font-family:&quot;Open Sans&quot;,sans-serif;color:#500000">{event_name_uppercase}</span></a></b><br>
                                                    <span style="font-size:9.0pt;font-family:&quot;Open Sans&quot;,sans-serif">{event_date}, {event_location}<br>
                                                    Time: {event_time}<br>
                                                    <b>Facilitators</b>: {event_facilitators}<br>
                                                    <b>Description</b>: {short_description}</span><br>
                                                    <b><span style="font-size:9.0pt;font-family:&quot;Open Sans&quot;,sans-serif"><a href="{event_link}" style="text-decoration:underline;color:#500000" target="_blank"><span style="font-family:&quot;Open Sans&quot;,sans-serif;color:#500000">Read more about the {event_name_short} event here</span></a></span></b><span style="font-size:9.0pt;font-family:&quot;Open Sans&quot;,sans-serif">.<br>
                                                    <b><a href="{event_registration_link}" style="text-decoration:underline;color:#500000" target="_blank"><span style="font-family:&quot;Open Sans&quot;,sans-serif;color:#500000">Register for the {event_name_short} event here</span></a></b>.</span><u></u><u></u>
                                                </p>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
        """
    
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