"""Stage 3 solution - add a tool + let the agent loop.

Now the agent stops being a Q&A box and starts DOING work: we give it a tool
(a Python function it can choose to call) that queries the LIVE ClinicalTrials.gov
API. Once the tool is registered, Strands runs the reason -> act -> observe loop
automatically: the agent decides to call the tool, reads the results, filters them
against the patient, and returns a ranked, actionable shortlist.

Complete reference version of agent.py after Stage 3. Built up in three steps:
  Step 1 - add the search_clinical_trials() function (calls the live API).
  Step 2 - register it as a tool and update the system prompt.
  Step 3 - re-run and ask the same question -> a ranked shortlist.
"""

import json
import os

import requests
from strands import Agent, tool
from strands.models import BedrockModel

import sys

# Let `python solutions/stageN_agent.py` find config.py in the project root.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from config import MODEL_ID, REGION

QUESTION = (
    "I'm a 55-year-old female ER+/HER2- disease free breast cancer survivor "
    "who has been on letrozole for 7 years and now is suffering from severe "
    "side effects. Are there clinical trials I might qualify for?"
)

_CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cached_trials.json")
_API = "https://clinicaltrials.gov/api/v2/studies"


@tool
def search_clinical_trials(
    condition: str,
    status: str = "RECRUITING",
    phase: str = "",
    location: str = "",
) -> dict:
    """Search ClinicalTrials.gov for trials matching a condition.

    Args:
        condition: The medical condition to search for, e.g. "HER2-positive
            metastatic breast cancer".
        status: Recruitment status filter, e.g. "RECRUITING" (default).
        phase: Optional trial phase filter, e.g. "PHASE2".
        location: Optional location filter, e.g. "United States".

    Returns:
        A dict with the matching studies (NCT id, title, status, phase,
        conditions, and locations). Falls back to a bundled snapshot if the
        live API is unreachable, so the tool always returns results.
    """
    params = {
        "query.cond": condition,
        "pageSize": 10,
        "fields": "NCTId,BriefTitle,OverallStatus,Phase,Condition,LocationCity,LocationCountry",
    }
    if status:
        params["filter.overallStatus"] = status
    if location:
        params["query.locn"] = location
    try:
        resp = requests.get(_API, params=params, timeout=8)
        resp.raise_for_status()
        return {"source": "live", "results": resp.json().get("studies", [])}
    except Exception:
        # Live-API fallback: return the bundled snapshot so Stage 3 always works.
        with open(_CACHE_PATH) as fh:
            return {"source": "cached", "results": json.load(fh)["studies"]}


SYSTEM_PROMPT = """You are a clinical-trials assistant helping a patient explore
options. Use the search_clinical_trials tool to find currently recruiting trials
that match the patient's condition. Then filter the results against the patient's
profile and return a RANKED shortlist. For each trial include: name, NCT ID,
recruiting status, location, and a one-line 'why it might fit' plus next steps.
Be clear and compassionate."""


def build_agent():
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION, temperature=0.3)
    # Registering the tool is all it takes - Strands runs the loop for us.
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[search_clinical_trials],
        callback_handler=None,
    )


def main():
    agent = build_agent()
    result = agent(QUESTION)
    print(str(result))


if __name__ == "__main__":
    main()
