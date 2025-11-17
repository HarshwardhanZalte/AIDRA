from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AnalysisResult(BaseModel):
    """
    Pydantic model for a single analysis result.
    """
    disaster_type: str
    risk_level: str
    lives_in_danger: bool
    analysis: str
    timestamp: str

class SessionData(BaseModel):
    """
    Defines the structure of data stored in a session.
    """
    session_id: str
    previous_analyses: List[AnalysisResult] = []
    user_interactions: List[str] = []
    
    def add_analysis(self, result: AnalysisResult):
        self.previous_analyses.append(result)
        # Optional: Keep only the last N analyses
        self.previous_analyses = self.previous_analyses[-10:] 
        
    def add_interaction(self, interaction: str):
        self.user_interactions.append(interaction)
        self.user_interactions = self.user_interactions[-20:]