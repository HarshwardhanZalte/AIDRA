import json
from google.generativeai.types import FunctionDeclaration, Tool
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# A simple "database" of emergency contacts.
# In a real app, this would be a proper database or external API.
EMERGENCY_CONTACTS_DB = {
    "india": {
        "default": {
            "Police": "100",
            "Fire Brigade": "101",
            "Ambulance": "102",
            "National Disaster Helpline": "108",
            "Women Helpline": "1091",
        },
        "fire": {
            "Fire Brigade": "101",
            "Ambulance": "102",
            "Police": "100",
        },
        "flood": {
            "National Disaster Helpline": "108",
            "State Disaster Management": "1070",
            "Flood Control Room": "1077",
        },
        "road_accident": {
            "Ambulance": "102",
            "Police": "100",
            "Road Accident Helpline": "1073",
        },
        "building_collapse": {
            "National Disaster Helpline": "108",
            "Fire Brigade": "101",
            "Ambulance": "102",
        },
        "chemical_leak": {
            "National Disaster Helpline": "108",
            "Chemical Hazard Control": "1078",
            "Fire Brigade": "101",
        }
    },
    "usa": {
        "default": {
            "Emergency": "911",
        },
        "fire": {"Emergency": "911"},
        "flood": {"Emergency": "911", "FEMA": "1-800-621-3362"},
        "road_accident": {"Emergency": "911"},
    },
    # Add more countries as needed
}

def get_emergency_contacts(country: str, disaster_type: str = "default") -> str:
    """
    Retrieves emergency contact numbers for a given country and disaster type.
    
    Args:
        country: The country to get contacts for (e.g., "India", "USA").
        disaster_type: The specific type of disaster (e.g., "fire", "flood").
    
    Returns:
        A JSON string of emergency contacts.
    """
    logger.info(f"Tool: Searching contacts for country='{country}', type='{disaster_type}'")
    
    country_key = country.lower()
    disaster_key = disaster_type.lower().replace(" ", "_")

    if country_key not in EMERGENCY_CONTACTS_DB:
        logger.warning(f"Country '{country}' not in DB. Returning default.")
        return json.dumps({"error": f"Contacts for {country} not found."})

    country_data = EMERGENCY_CONTACTS_DB[country_key]
    
    # Get disaster-specific numbers
    contacts = country_data.get(disaster_key)
    
    # If no specific numbers, get default numbers for that country
    if not contacts:
        contacts = country_data.get("default")
        
    logger.info(f"Tool: Found contacts: {contacts}")
    return json.dumps(contacts)


def get_emergency_contacts_tool() -> Tool:
    """
    Returns the ADK/Gemini-compatible Tool object.
    """
    return Tool(
        function_declarations=[
            FunctionDeclaration(
                name="get_emergency_contacts",
                description="Fetches emergency contact numbers (Police, Fire, Ambulance, etc.) for a specific country and disaster type.",
                parameters={
                    "type": "OBJECT",
                    "properties": {
                        "country": {
                            "type": "STRING",
                            "description": "The country to search for, e.g., 'India', 'USA'.",
                        },
                        "disaster_type": {
                            "type": "STRING",
                            "description": "The type of disaster, e.g., 'fire', 'flood', 'road_accident'. Defaults to 'default' if not specified.",
                        }
                    },
                    "required": ["country"]
                },
            )
        ],
        function_callable=get_emergency_contacts # This is not directly used by Gemini, but good practice.
        # The new `google-generativeai` library prefers passing the function itself.
        # However, the ADK pattern often involves a dispatcher.
        # For simplicity with the latest Gemini API, we'll pass the function *map*
        # to the model in the agent.
    )

# We export the function itself for the agent's tool config
EMERGENCY_CONTACTS_TOOL_FUNCTION = get_emergency_contacts