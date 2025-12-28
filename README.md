# AIDRA: AI Disaster Response Assistant

## The Problem
People face critical life-or-death decisions in the first moments of disasters (fires, floods, accidents) but don't know:
- Should I run or hide?
- What hazards exist?
- Who to call?

## The Solution
A web app where users upload a photo of an emergency and instantly receive a complete response plan including:
- Disaster type & risk level
- Immediate evacuation/safety instructions
- Local emergency contacts
- Step-by-step actions

## Why Multi-Agent?
Instead of one unreliable AI prompt, AIDRA uses **3 specialized agents** working in sequence:

1. **Image Agent**: Analyzes the photo, identifies disaster type and hazards
2. **Safety Agent**: Generates actionable safety advice based on the analysis
3. **Response Agent**: Creates final instructions with risk assessment

## Key Features Implemented
- **Multi-agent system**: Sequential chain of specialized AI agents
- **Custom tool**: Database lookup for local emergency numbers (101 for India, 911 for USA)
- **Session memory**: Tracks user interactions and previous reports
- **Logging**: Complete observability for debugging and reliability

## Tech Stack
FastAPI backend + Streamlit frontend + Gemini models + structured JSON outputs

**Result**: Reliable, life-saving guidance in seconds during critical emergencies.
