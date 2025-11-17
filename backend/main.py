import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any

from backend.utils.logger import get_logger
from backend.agents.image_agent import ImageUnderstandingAgent
from backend.agents.safety_agent import SafetyMeasuresAgent
from backend.agents.response_agent import EmergencyResponseAgent
from backend.agents.agent_orchestrator import AIDRAOrchestrator, FullAnalysisResponse
from backend.services.session_service import session_service, InMemorySessionService
from backend.tools.emergency_database_tool import EMERGENCY_CONTACTS_TOOL_FUNCTION

# Load environment variables from .env file
load_dotenv()

# --- Configuration & Initialization ---

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found in .env file. Please add it.")

logger = get_logger(__name__)

# --- App Setup ---
app = FastAPI(
    title="AI Disaster Response Assistant (AIDRA)",
    description="Analyzes disaster images to provide safety and response information.",
    version="1.0.0"
)

# Add CORS middleware to allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Global Components (Singleton Pattern) ---
# We initialize all components once when the app starts.

try:
    # # 1. Tools
    # # The 'tools' argument for the Gemini model needs a map of name:function
    # 1. Tools (No longer needed here)

    # 2. Agents
    image_agent = ImageUnderstandingAgent(api_key=API_KEY)
    safety_agent = SafetyMeasuresAgent(api_key=API_KEY)
    # FIX: Response agent no longer takes tools
    response_agent = EmergencyResponseAgent(api_key=API_KEY)
    
    # 3. Session Service (imported as singleton)
    
    # 4. Orchestrator
    orchestrator = AIDRAOrchestrator(
        image_agent=image_agent,
        safety_agent=safety_agent,
        response_agent=response_agent,
        session_service=session_service
    )
    logger.info("Application startup successful. All components initialized.")
except Exception as e:
    logger.critical(f"FATAL: Failed to initialize components: {e}")
    # Application will be in a broken state, but FastAPI will still run.
    # We'll rely on endpoint errors to notify the user.
    orchestrator = None 

# --- API Endpoints ---

@app.get("/health", summary="Health Check")
def get_health():
    """
    Simple health check endpoint.
    """
    if orchestrator is None:
        return {"status": "unhealthy", "error": "Orchestrator failed to initialize."}
    return {"status": "ok"}

@app.post("/analyze/", 
          summary="Analyze Disaster Image", 
          response_model=FullAnalysisResponse)
async def analyze_image(
    image: UploadFile = File(..., description="The image of the disaster scene."),
    country: str = Form("India", description="User's country (for emergency numbers)."),
    x_session_id: Optional[str] = Header(None, description="The user's session ID for memory.")
):
    """
    Upload an image to get a full disaster analysis.

    This endpoint orchestrates the multi-agent system:
    1.  **Image Agent:** Analyzes the image.
    2.  **Safety Agent:** Generates safety precautions.
    3.  **Response Agent:** Generates step-by-step instructions and contacts.
    
    Session memory is tracked using the `X-Session-ID` header.
    """
    if orchestrator is None:
        raise HTTPException(status_code=500, detail="Server components failed to initialize.")

    # 1. Get image bytes
    try:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Image file is empty.")
    except Exception as e:
        logger.error(f"Failed to read image file: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

    # 2. Manage Session ID
    session_id = x_session_id or str(uuid.uuid4())
    logger.info(f"Processing request for session: {session_id}")

    # 3. Run Orchestrator
    try:
        analysis_result = await orchestrator.run_analysis(
            session_id=session_id,
            image_bytes=image_bytes,
            country=country
        )
        return analysis_result
    except Exception as e:
        logger.error(f"Analysis failed for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

@app.get("/session/{session_id}", summary="Get Session Memory")
def get_session_memory(session_id: str):
    """
    Retrieves the stored data for a specific session.
    """
    try:
        session_data = session_service.get_session(session_id)
        if not session_data.previous_analyses and not session_data.user_interactions:
             raise HTTPException(status_code=404, detail="Session not found or is empty.")
        return session_data
    except Exception as e:
        logger.error(f"Failed to retrieve session {session_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

if __name__ == "__main__":
    import uvicorn
    # This is for debugging only. Use `run.sh` or `uvicorn` command in production.
    logger.info("Starting server in debug mode...")
    uvicorn.run(app, host="0.0.0.0", port=8000)