import google.generativeai as genai
import os
import json
from pydantic import BaseModel, Field
from typing import List
from PIL import Image
import io
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Pydantic model for the agent's expected JSON output
class ImageAnalysisOutput(BaseModel):
    disaster_type: str = Field(..., description="Type of disaster (e.g., 'Structural Fire', 'Flash Flood', 'Road Accident').")
    hazards: List[str] = Field(..., description="List of visible hazards (e.g., 'Heavy Smoke', 'Rising Water', 'Damaged Vehicle').")
    severity_score: int = Field(..., description="A score from 0-100 indicating the disaster's severity.")
    detailed_analysis: str = Field(..., description="A detailed explanation of what is happening in the image.")

class ImageUnderstandingAgent:
    """
    Agent 1: Analyzes the uploaded image using Gemini Vision.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction="You are a precise, analytical disaster assessment AI. Your sole purpose is to analyze an image and return a structured JSON object. You will not say anything else. You will not add 'Here is the JSON' or any other conversational text. You respond ONLY with the valid JSON."
        )
        logger.info("ImageUnderstandingAgent initialized with gemini-2.5-flash.")

    async def analyze(self, image_bytes: bytes) -> ImageAnalysisOutput:
        """
        Analyzes the image and returns a structured JSON output.
        """
        logger.info("ImageUnderstandingAgent: Starting analysis...")
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # This is the prompt that instructs the model to return JSON
            # matching the Pydantic model's schema.
            prompt = f"""
            Analyze the provided disaster image. Based *only* on what you see, provide a JSON response matching this schema:

            {ImageAnalysisOutput.model_json_schema()}

            **Analysis Checklist:**
            1.  **disaster_type**: What is the primary disaster? (e.g., "Structural Fire", "Flash Flood", "Road Accident").
            2.  **hazards**: What specific dangers are visible? (e.g., "Heavy smoke", "Submerged vehicles", "Damaged power lines").
            3.  **severity_score**: On a scale of 0 (minor) to 100 (catastrophic), how severe is this?
            4.  **detailed_analysis**: A 2-3 sentence technical description of the scene.
            """
            
            response = await self.model.generate_content_async(
                [prompt, image],
                generation_config={"response_mime_type": "application/json"} # Force JSON output
            )
            
            # Parse the JSON response
            response_text = response.text
            logger.debug(f"ImageAgent Raw Response: {response_text}")
            
            json_data = json.loads(response_text)
            
            # Validate with Pydantic
            analysis_output = ImageAnalysisOutput(**json_data)
            logger.info("ImageUnderstandingAgent: Analysis successful.")
            
            return analysis_output
            
        except Exception as e:
            logger.error(f"ImageUnderstandingAgent: Error during analysis: {e}")
            logger.error(f"Raw response was: {response.text if 'response' in locals() else 'N/A'}")
            # Fallback in case of error
            return ImageAnalysisOutput(
                disaster_type="Unknown",
                hazards=["Analysis Error"],
                severity_score=0,
                detailed_analysis=f"An error occurred during image analysis: {str(e)}"
            )