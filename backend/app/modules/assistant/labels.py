"""Map a message onto the evaluation labels, using the real assistant.

Labels are the harness's names, not clinical judgements. SMS channel is used so
web-only retrieval does not change the score.
"""

from app.modules.assistant.schemas import AssistantRequest
from app.modules.assistant.service import handle_message

_FLAGS = (
    ("fear_of_diagnosis", "fear"),
    ("fear_of_procedure_pain", "fear"),
    ("cost", "cost"),
    ("transport_access", "transport"),
    ("stigma_privacy", "stigma"),
    ("no_info_where_to_go", "dont_know_where"),
)


def classify(text: str) -> str:
    response = handle_message(AssistantRequest(channel="sms", text=text))
    if response.safety.level == "crisis":
        return "crisis"
    if response.safety.level == "diagnosis_request":
        return "diagnosis_request"
    flags = {item.flag for item in response.barrier_flags}
    for flag, label in _FLAGS:
        if flag in flags:
            return label
    return "none"
