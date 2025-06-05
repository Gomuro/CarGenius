from fake_useragent import UserAgent
import random
import re

def validate_user_agent(user_agent: str) -> bool:
    """
    Validates if the user agent string is in a correct format.
    Returns True if valid, False otherwise.
    """
    # Basic validation pattern for user agents
    pattern = r'^Mozilla/[\d.]+ \(.*\) .*$'
    return bool(re.match(pattern, user_agent))

def generate_random_user_agent():
    """
    Generates a random user agent string.
    Returns a string representing a random browser's user agent.
    """
    try:
        ua = UserAgent()
        return ua.random
    except Exception as e:
        # Fallback to a list of common user agents if the library fails
        fallback_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        return random.choice(fallback_agents) 