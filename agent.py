"""From Zero to Secure Agent - your starting point (Stage 1: the baseline agent).

This is the whole agent. It has three parts:
  1. a MODEL      - Claude Sonnet 4.5, running on Amazon Bedrock
  2. a SYSTEM PROMPT - the standing instructions that shape how it answers
  3. a RUN step   - we hand it the patient's question and print the answer

Run it:   python agent.py

Right now the model answers from training data alone - no access to real,
current clinical trials. Notice how vague (and sometimes made-up) the answer is.
Over the next two stages you'll fix that: Stage 2 grounds it in a Knowledge Base
of real trials, and Stage 3 lets it call the live ClinicalTrials.gov API.
"""

from strands import Agent
from strands.models import BedrockModel

from config import MODEL_ID, REGION

# --- 2. The system prompt: who the agent is and how it should behave ---------
SYSTEM_PROMPT = """You are a clinical-trials assistant helping a patient explore
options. Be clear and compassionate. When you mention a clinical trial, give its
name and NCT ID. If you are not certain a trial is real and currently enrolling,
say so plainly rather than guessing."""

# The single question we ask at every stage of the workshop.
QUESTION = (
    "I'm a 55-year-old female ER+/HER2- disease free breast cancer survivor "
    "who has been on letrozole for 7 years and now is suffering from severe "
    "side effects. Are there clinical trials I might qualify for?"
)


def build_agent():
    # --- 1. The model: Claude Sonnet 4.5 on Amazon Bedrock -------------------
    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=REGION,
        temperature=0.3,
    )
    # Assemble the agent from the model + the system prompt.
    # callback_handler=None turns off Strands' live token streaming so we print
    # the final answer once, cleanly, ourselves.
    return Agent(model=model, system_prompt=SYSTEM_PROMPT, callback_handler=None)


def main():
    agent = build_agent()
    # --- 3. Run: ask the question and print the final answer -----------------
    result = agent(QUESTION)
    print(str(result))


if __name__ == "__main__":
    main()
