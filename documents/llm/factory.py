import os
from .remote import RemoteLLM
from .local import LocalLLM

def get_llm_backend():
    backend = os.getenv("LLM_BACKEND", "remote")
    return RemoteLLM() if backend == "remote" else LocalLLM()