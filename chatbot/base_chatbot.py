from abc import ABC, abstractmethod


class BaseChatbot(ABC):

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def ask(self, question: str) -> str:
        pass

    @abstractmethod
    def close(self):
        pass