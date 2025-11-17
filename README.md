# 🚨 AI Disaster Response Assistant (AIDRA)
## Problem

In the first critical moments of a disaster be it a building fire, a flash flood, or a multi-car accident there is a terrifying and dangerous **information gap**. People on the scene are often in a state of panic, and first responders are minutes, not seconds, away. The actions taken in these first few moments can be the difference between life and death.

**Critical Questions:**
- Should I run or hide?
- Is it safer to go upstairs or get to the ground floor?
- What are the specific hazards I can't see?
- Who is the right authority to call for this specific situation?

---

## Solution

AIDRA is a complete web application built on a sophisticated multi-agent system. Here is the user's journey:

### User Journey

1.  **Upload**: A user witnesses an incident (e.g., a chemical spill on a highway). They open the AIDRA web app (a Streamlit frontend) and upload a photo.

2.  **Analyze**: The user's image is sent to our FastAPI backend, where it's handed off to our AI agent orchestrator.

3.  **Respond**: In seconds, the frontend displays a complete, easy-to-read emergency response plan.

### Sample Response

This is not just a single-prompt response. The user receives a full, structured analysis:

**Disaster Type:** Structural Fire (Confidence: 95%)

**Risk Level:** Critical

**Lives in Danger:** Yes

**Immediate Instructions:**
- EVACUATE immediately. Do not stop to collect belongings.
- Call emergency services (101 for Fire) NOW.
- Stay low to the ground to avoid smoke inhalation.

**Safety Measures:**
- Cover your mouth and nose with a wet cloth.
- Do not use elevators.

**Emergency Contacts (India):**
- Fire Brigade: 101
- Police: 100
- Ambulance: 102

---

## Architecture

### Why a Multi-Agent System?

A single, monolithic LLM prompt is not reliable enough for a life-or-death situation. A single prompt for a task this complex often fails, hallucinates, or misses critical steps.

The use of agents is central and meaningful to our solution. We adopted a **multi-agent architecture** for specialization and reliability. We broke the complex problem of "disaster response" into a logical chain of specialized tasks, each handled by an agent with a specific persona and function. This ensures each part of the analysis is handled by an "expert," leading to a final response that is far more accurate, reliable, and safe.

---

### The Implementation: An ADK-Powered Architecture

AIDRA is a production-grade codebase that demonstrates a deep and practical application of the concepts from the 5-Day Intensive Course. We successfully implemented four of the key competition features.

Our architecture is a **Sequential Agent Orchestrator** (`agent_orchestrator.py`) that manages the flow of data between three specialized, Gemini-powered agents, a custom tool, and a session-based memory service.

```
[User Image] → [Agent 1: Image] → [Agent 2: Safety] → [Tool: Contacts] → [Agent 3: Response] → [Final JSON to User]
```

#### 1. Feature: Multi-agent System (Sequential Agents)

Our orchestrator coordinates a three-agent sequence. Each agent is an independent Python class, powered by a Gemini model, with a specific system prompt and task.

##### Agent 1: ImageUnderstandingAgent
- **Model:** gemini-2.5-flash-lite (or other multimodal model)
- **Persona:** A precise, analytical disaster assessment AI
- **Task:** This agent is the only one that sees the image. Its sole job is to analyze the visual data and return a structured JSON object with its findings: `{disaster_type, hazards, severity_score, detailed_analysis}`. This Pydantic-validated object is then passed to the next agent.

##### Agent 2: SafetyMeasuresAgent
- **Model:** gemini-2.5-flash-lite (or other text model)
- **Persona:** A disaster preparedness expert and public safety advisor
- **Task:** This agent receives the JSON analysis from Agent 1. It does not see the image. Its task is to read the hazards and disaster_type and generate a new JSON object containing concise, actionable safety advice: `{personal_safety, preventive_actions, risk_mitigation_checklist}`.

##### Agent 3: EmergencyResponseAgent
- **Model:** gemini-2.5-flash-lite (or other text model)
- **Persona:** A calm, authoritative emergency response dispatcher
- **Task:** This is the final synthesizer. It receives the outputs from both Agent 1 and Agent 2, as well as the data from our custom tool. It performs the final risk assessment (risk_level, lives_in_danger) and generates the step-by-step instructions and "what to say" script for the end-user.

#### 2. Feature: Custom Tools

To provide real-world, localized value, we built a **Custom Tool** (`emergency_database_tool.py`).

- **Function:** This tool is a simple Python function that mimics a database. It takes a country and disaster_type as input and returns a JSON object of the correct, localized emergency contact numbers (e.g., 101 for Fire in India, 911 for all in the USA).

- **Integration:** The orchestrator calls this tool after the disaster type is known. This ensures the AI's response is grounded in factual, non-LLM data, which is critical for emergency contacts.

#### 3. Feature: Sessions & Memory (Sessions & State Management)

AIDRA is a stateful application. We implemented an **InMemorySessionService** to demonstrate session management.

- **Function:** The FastAPI backend and Streamlit frontend communicate using an `X-Session-ID` header.

- **Memory:** Our `session_service.py` maintains a simple in-memory dictionary. After each successful analysis, the AIDRAOrchestrator saves the key findings (disaster_type, risk_level, timestamp) to the user's session.

- **Value:** This fulfills the "Sessions & Memory" requirement and provides a foundation for more complex, long-term memory (e.g., "I see you reported a fire 10 minutes ago. Has the situation changed?").

#### 4. Feature: Observability (Logging)

A project of this complexity is impossible to debug without good observability.

- **Function:** We implemented a central `logger.py` utility that is instantiated by every agent, service, and orchestrator.

- **Value:** This structured logging provides a complete trace of the agent's "thinking" process. During development, this was essential for diagnosing 404 model errors, tool-use failures, and request timeouts. It's not just an add-on; it's a critical part of a production-ready agent system.

---

### 4. Bonus: Effective Use of Gemini

We leveraged the Gemini models to their full potential:

- **Multimodality:** The ImageUnderstandingAgent uses Gemini's vision capability to perform complex scene analysis, a task impossible for a text-only model.

- **Strict JSON Output:** We used robust system prompts and the `generation_config={"response_mime_type": "application/json"}` (where supported, or strong prompt engineering) to force the agents to return valid JSON. This output is immediately parsed and validated by Pydantic models, ensuring a clean, reliable data-contract between agents.

---

# AIDRA Setup and Run Guide

## 1. Prerequisites

Before you start, make sure you have:
* Python 3.10+ installed
* Your Google Gemini API Key

---

## 2. Setup (One-Time)

Follow these steps to set up your project environment.

### Create a Virtual Environment
Open your terminal in the `aidra` folder and run:

```bash
python -m venv venv
```

### Activate the Environment
* **On Windows:** 
  ```bash
  venv\Scripts\activate
  ```
* **On macOS/Linux:** 
  ```bash
  source venv/bin/activate
  ```

### Install Dependencies
With your environment active, install all required libraries:

```bash
pip install -r backend/requirements.txt
```

### Set Your API Key
1. Copy the example file: 
   ```bash
   cp .env.example .env
   ```
   (or just rename it)
   
2. Open the `.env` file and paste your Gemini API key:
   ```
   GEMINI_API_KEY="YOUR_API_KEY_HERE"
   ```

---


## 3. How to Run 

If you prefer to run them separately, open two terminals (and activate your `venv` in both).

### ➡️ In Terminal 1 (Backend)

Run the FastAPI server:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Leave this running.

### ➡️ In Terminal 2 (Frontend)

Run the Streamlit app:

```bash
streamlit run frontend/app.py
```

This will automatically open your browser.

---

## 5. Access the App

Once running, open your web browser and go to:

```
http://localhost:8501
```