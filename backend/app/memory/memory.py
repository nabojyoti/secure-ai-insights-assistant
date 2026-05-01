from collections import deque

class ConversationMemory:

    def __init__(self):
        self.history = deque(maxlen=5)

    def add(self, q, a):
        self.history.append((q, a))