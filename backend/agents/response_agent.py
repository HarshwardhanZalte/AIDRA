import google.generativeai as genai
import os
import json
from pydantic import BaseModel, Field
from typing import List, Dict, Callable
from backend.utils.logger import get_logger
from backend.agents.image_agent import ImageAnalysisOutput
from backend.agents.safety_agent import SafetyMeasuresOutput
from backend.tools.emergency_database_tool import EMERGENCY_CONTACTS_TOOL_FUNCTION

logger = get_logger(__name__)

class FinalResponseOutput(BaseModel):
    risk_level: str = Field(..., description="The final assessed risk level (Low, Medium, High, Critical).")
    lives_in_danger: bool = Field(..., description="Whether human lives appear to be in immediate danger.")
    step_by_step_instructions: List[str] = Field(..., description="A numbered list of immediate, clear steps for the user.")
    what_to_say: str = Field(..., description="A script for what to tell emergency services.")
    emergency_contacts: Dict[str, str] = Field(..., description="A dictionary of emergency contacts.")

# class EmergencyResponseAgent:
#     """
#     Agent 3: Synthesizes all information, uses tools, and generates the final response.
#     """
#     def __init__(self, api_key: str, tool_map: Dict[str, Callable]):
#         self.api_key = api_key
#         genai.configure(api_key=self.api_key)
        
#         # Pass the tool functions to the model
#         self.model = genai.GenerativeModel(
#             model_name="gemini-1.5-pro",
#             system_instruction="You are a calm, authoritative emergency response dispatcher. Your job is to provide a final, unified response plan. You MUST use your tools to find contact numbers.",
#             tools=tool_map # Pass the tool functions
#         )
#         logger.info("EmergencyResponseAgent initialized with tools.")

class EmergencyResponseAgent:
    """
    Agent 3: Synthesizes all information, uses tools, and generates the final response.
    """
    def __init__(self, api_key: str): # <-- FIX: Changed arg name
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        
        # Pass the tool functions to the model
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-lite",
            system_instruction="You are a calm, authoritative emergency response dispatcher. Your job is to synthesize all available information into a single, complete, final response plan for a civilian. You must follow instructions precisely. You respond ONLY with a valid JSON object. Do not add any other text."
        )
        logger.info("EmergencyResponseAgent initialized with tools.")

    async def generate_response(
        self,
        analysis: ImageAnalysisOutput,
        safety_measures: SafetyMeasuresOutput,
        country: str,
        contacts: dict  
    ) -> FinalResponseOutput:
        """
        Generates the final, comprehensive response.
        """
        logger.info(f"EmergencyResponseAgent: Generating final response for {analysis.disaster_type} in {country}")
        
        # Convert contacts dict to a string for the prompt
        contacts_str = json.dumps(contacts, indent=2)

        prompt = f"""
        You are an AI Disaster Response Assistant. Synthesize all the information below into a final, actionable plan.
        
        **Context:**
        -   **User's Country:** {country}
        -   **Disaster Type:** {analysis.disaster_type}
        -   **Severity:** {analysis.severity_score}/100
        -   **Hazards:** {', '.join(analysis.hazards)}
        -   **Analysis:** {analysis.detailed_analysis}
        -   **Safety Measures:** {safety_measures.model_dump_json(indent=2)}
        -   **Emergency Contacts (Use these):**
            {contacts_str}

        **Your Task:**
        1.  **Assess Final Risk:** Determine a final `risk_level` (Low, Medium, High, Critical).
        2.  **Assess Life Risk:** Determine if `lives_in_danger` (true/false).
        3.  **Generate Steps:** Create `step_by_step_instructions` for the user.
        4.  **Create Script:** Provide a `what_to_say` script for the user.
        5.  **Include Contacts:** Copy the `emergency_contacts` provided above *exactly* into the output.

        **Output Format:**
        Respond *only* with a valid JSON object matching this schema:
        {FinalResponseOutput.model_json_schema()}
        """
        
        try:
            # FIX: Simple call, no tool logic
            response = await self.model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            response_text = response.text
            logger.debug(f"ResponseAgent Raw Response: {response_text}")
            
            json_data = json.loads(response_text)
            
            # Ensure contacts are present, though the prompt should handle this
            if "emergency_contacts" not in json_data or not json_data["emergency_contacts"]:
                json_data["emergency_contacts"] = contacts
                
            final_output = FinalResponseOutput(**json_data)
            logger.info("EmergencyResponseAgent: Final response generated successfully.")
            return final_output

        except Exception as e:
            logger.error(f"EmergencyResponseAgent: Error generating response: {e}")
            logger.error(f"Raw response was: {response.text if 'response' in locals() else 'N/A'}")
            # Fallback
            return FinalResponseOutput(
                risk_level="Unknown",
                lives_in_danger=False,
                step_by_step_instructions=["Error generating final response. Please call your local emergency services immediately."],
                what_to_say=f"There is an emergency of type {analysis.disaster_type}. My location is [Your Location].",
                emergency_contacts=contacts
            )