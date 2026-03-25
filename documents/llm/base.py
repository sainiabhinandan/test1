from abc import ABC, abstractmethod

class LLMBackend(ABC):
    @abstractmethod
    def classify(self, text: str) -> dict:
        pass