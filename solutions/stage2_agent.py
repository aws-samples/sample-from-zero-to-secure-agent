"""Stage 2 solution - grounding the agent with RAG (a Bedrock Knowledge Base).

Same model, same question as Stage 1 - but before we ask the model, we RETRIEVE
the most relevant real trial documents from a pre-built Amazon Bedrock Knowledge
Base and inject them into the system prompt as grounding. That's RAG:
Retrieval-Augmented Generation.

This is a complete reference version of agent.py after Stage 2. During the
workshop you build up to this in three small steps:
  Step 1 - add retrieve_trials() and just PRINT what comes back (see the docs).
  Step 2 - inject the retrieved text into the system prompt as grounding.
  Step 3 - re-run and ask the same question -> grounded, cited answer.
"""

import boto3
from strands import Agent
from strands.models import BedrockModel

import os
import sys

# Let `python solutions/stageN_agent.py` find config.py in the project root.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from config import MODEL_ID, REGION, KNOWLEDGE_BASE_ID

QUESTION = (
    "I'm a 55-year-old female ER+/HER2- disease free breast cancer survivor "
    "who has been on letrozole for 7 years and now is suffering from severe "
    "side effects. Are there clinical trials I might qualify for?"
)


def retrieve_trials(question, k=5):
    """Ask the Knowledge Base for the k most relevant trial documents.

    This is the 'R' in RAG. It's a plain Bedrock API call - no magic. The KB was
    built ahead of time by indexing ~50 real ClinicalTrials.gov documents.
    """
    client = boto3.client("bedrock-agent-runtime", region_name=REGION)
    response = client.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": question},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": k}
        },
    )
    return [r["content"]["text"] for r in response["retrievalResults"]]


# The system prompt now tells the model to answer ONLY from the retrieved trials.
SYSTEM_PROMPT_TEMPLATE = """You are a clinical-trials assistant helping a patient
explore options. Answer ONLY using the clinical-trial documents provided below.
For every trial you mention, give its title exactly as written in the documents
and its NCT ID - do not add acronyms or nicknames. If the documents don't contain
a good match, say so plainly - do not invent trials.

RETRIEVED CLINICAL TRIALS:
{grounding}
"""


def build_agent(grounding_text):
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION, temperature=0.3)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(grounding=grounding_text)
    return Agent(model=model, system_prompt=system_prompt, callback_handler=None)


def main():
    # Step 1 (during the lab): print to see retrieval working.
    trials = retrieve_trials(QUESTION)
    print(f"Retrieved {len(trials)} trial document(s) from the Knowledge Base.\n")

    # Step 2: inject the retrieved documents as grounding.
    grounding = "\n\n---\n\n".join(trials)
    agent = build_agent(grounding)

    # Step 3: ask the same question - now grounded and cited.
    result = agent(QUESTION)
    print(str(result))


if __name__ == "__main__":
    main()
