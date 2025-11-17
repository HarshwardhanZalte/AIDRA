from backend.agents.image_agent import ImageUnderstandingAgent, ImageAnalysisOutput
from backend.agents.safety_agent import SafetyMeasuresAgent, SafetyMeasuresOutput
from backend.agents.response_agent import EmergencyResponseAgent, FinalResponseOutput
from backend.services.session_service import InMemorySessionService
from backend.services.memory_service import AnalysisResult
from backend.utils.logger import get_logger
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import json
from backend.tools.emergency_database_tool import EMERGENCY_CONTACTS_TOOL_FUNCTION

logger = get_logger(__name__)

class FullAnalysisResponse(BaseModel):
    """
    The final, unified response object returned by the API.
    """
    session_id: str
    disaster_type: str
    confidence: float # From severity score
    risk_level: str
    lives_in_danger: bool
    analysis: str
    instructions: List[str]
    safety_measures: SafetyMeasuresOutput
    contacts: Dict[str, str]

class AIDRAOrchestrator:
    """
    Manages the sequential execution of the agent chain.
    This class is the "Sequential Agent" implementation.
    """
    def __init__(
        self,
        image_agent: ImageUnderstandingAgent,
        safety_agent: SafetyMeasuresAgent,
        response_agent: EmergencyResponseAgent,
        session_service: InMemorySessionService
    ):
        self.image_agent = image_agent
        self.safety_agent = safety_agent
        self.response_agent = response_agent
        self.session_service = session_service
        logger.info("AIDRAOrchestrator initialized with all agents and services.")

    async def run_analysis(
        self,
        session_id: str,
        image_bytes: bytes,
        country: str
    ) -> FullAnalysisResponse:
        """
        Executes the full agent sequence.
        Flow: Image Agent -> Safety Agent -> Response Agent
        """
        logger.info(f"Orchestrator: Starting analysis for session {session_id}")

        # --- Step 1: Image Understanding Agent ---
        image_analysis: ImageAnalysisOutput = await self.image_agent.analyze(image_bytes)
        logger.info(f"Orchestrator: Step 1/3 (Image) complete. Type: {image_analysis.disaster_type}")

        if image_analysis.disaster_type == "Unknown":
            # Short-circuit if analysis failed
            raise Exception("Image analysis failed to identify a disaster.")

        # --- Step 2: Safety Measures Agent ---
        safety_measures: SafetyMeasuresOutput = await self.safety_agent.generate_measures(image_analysis)
        logger.info(f"Orchestrator: Step 2/3 (Safety) complete.")

        # --- FIX: Step 2.5: Call Tool Manually ---
        logger.info(f"Orchestrator: Step 2.5/3 (Tool Call) complete.")
        try:
            contacts_json = EMERGENCY_CONTACTS_TOOL_FUNCTION(country, image_analysis.disaster_type)
            contacts_dict = json.loads(contacts_json)
        except Exception as e:
            logger.error(f"Orchestrator: Tool call failed: {e}. Using default.")
            contacts_json = EMERGENCY_CONTACTS_TOOL_FUNCTION(country, "default")
            contacts_dict = json.loads(contacts_json)


        # --- Step 3: Emergency Response Agent ---
        final_response: FinalResponseOutput = await self.response_agent.generate_response(
            analysis=image_analysis,
            safety_measures=safety_measures,
            country=country,
            contacts=contacts_dict  # <-- FIX: Pass contacts in
        )
        logger.info(f"Orchestrator: Step 3/3 (Response) complete. Risk: {final_response.risk_level}")

        # --- Step 4: Update Session Memory ---
        try:
            session_data = self.session_service.get_session(session_id)
            analysis_record = AnalysisResult(
                disaster_type=image_analysis.disaster_type,
                risk_level=final_response.risk_level,
                lives_in_danger=final_response.lives_in_danger,
                analysis=image_analysis.detailed_analysis,
                timestamp=datetime.utcnow().isoformat()
            )
            session_data.add_analysis(analysis_record)
            session_data.add_interaction(f"Analyzed {image_analysis.disaster_type} image.")
            self.session_service.save_session(session_data)
            logger.info(f"Orchestrator: Session {session_id} updated and saved.")
        except Exception as e:
            logger.error(f"Orchestrator: Failed to update session memory: {e}")
            # Continue anyway, as the response to the user is more critical

        # --- Step 5: Assemble Final API Response ---
        full_response = FullAnalysisResponse(
            session_id=session_id,
            disaster_type=image_analysis.disaster_type,
            confidence=image_analysis.severity_score, # Use severity as confidence
            risk_level=final_response.risk_level,
            lives_in_danger=final_response.lives_in_danger,
            analysis=image_analysis.detailed_analysis,
            instructions=final_response.step_by_step_instructions,
            safety_measures=safety_measures,
            contacts=final_response.emergency_contacts
        )
        
        logger.info(f"Orchestrator: Analysis complete for session {session_id}.")
        return full_response