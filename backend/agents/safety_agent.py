import google.generativeai as genai
import os
import json
from pydantic import BaseModel, Field
from typing import List
from backend.utils.logger import get_logger
from backend.agents.image_agent import ImageAnalysisOutput

logger = get_logger(__name__)

class SafetyMeasuresOutput(BaseModel):
    personal_safety: List[str] = Field(..., description="Immediate personal safety precautions.")
    preventive_actions: List[str] = Field(..., description="Preventive actions to mitigate further risk.")
    risk_mitigation_checklist: List[str] = Field(..., description="A simple checklist for the user.")

class SafetyMeasuresAgent:
    """
    Agent 2: Generates safety measures based on the image analysis.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-lite",
            system_instruction="You are a disaster preparedness expert and public safety advisor. Your job is to provide clear, actionable safety advice based on an analysis. You respond ONLY with a valid JSON object. Do not add any conversational text."
        )
        logger.info("SafetyMeasuresAgent initialized.")

    async def generate_measures(self, analysis: ImageAnalysisOutput) -> SafetyMeasuresOutput:
        """
        Generates safety measures based on the analysis from the ImageAgent.
        """
        logger.info(f"SafetyMeasuresAgent: Generating measures for {analysis.disaster_type}")
        
        prompt = f"""
        A disaster has been identified.
        
        **Analysis:**
        -   **Type:** {analysis.disaster_type}
        -   **Severity:** {analysis.severity_score}/100
        -   **Hazards:** {', '.join(analysis.hazards)}
        -   **Details:** {analysis.detailed_analysis}
        
        Based on this analysis, provide crucial safety information.
        Respond *only* with a valid JSON object matching this schema:
        
        {SafetyMeasuresOutput.model_json_schema()}
        
        Generate:
        1.  **personal_safety**: Immediate steps for personal protection.
        2.  **preventive_actions**: Actions to prevent the situation from worsening.
        3.  **risk_mitigation_checklist**: A simple to-do list for the user.
        """
        
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            response_text = response.text
            logger.debug(f"SafetyAgent Raw Response: {response_text}")
            
            json_data = json.loads(response_text)
            safety_output = SafetyMeasuresOutput(**json_data)
            
            logger.info("SafetyMeasuresAgent: Measures generated successfully.")
            return safety_output
            
        except Exception as e:
            logger.error(f"SafetyMeasuresAgent: Error generating measures: {e}")
            # Fallback
            return SafetyMeasuresOutput(
                personal_safety=["Error generating safety measures."],
                preventive_actions=["Error generating actions."],
                risk_mitigation_checklist=["Please contact authorities immediately."]
            )