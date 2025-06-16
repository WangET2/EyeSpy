from pathlib import Path
import os
from collections import deque
from abc import ABC, abstractmethod
import numpy as np
import czifile


'''
In practice, using collections.deque is faster due to being implemented in C.
class Node:
    def __init__(self, data: str, next: 'Node' = None):
        self.data = data
        self.next = next

'''

class BaseQueue(ABC):
    def __init__(self, directory: Path, *, enqueue_existing=False):
        self._directory = directory
        self._deque = deque()
        self._seen = set()
        for val in os.listdir(directory):
            if enqueue_existing:
                self.enqueue(val)
            else:
                self._seen.add(val)

    def is_empty(self) -> bool:
        return not self._deque

    def dequeue(self) -> None:
        self._deque.popleft()

    def update(self) -> None:
        for val in self._directory.iterdir():
            if val.is_file():
                self.enqueue(val.name)

    @abstractmethod
    def enqueue(self, val: str) -> None:
        pass

    @abstractmethod
    def front(self) -> np.ndarray:
        pass

class FileQueue(BaseQueue):
    def enqueue(self, val: str) -> None:
        if val in self._seen:
            return
        self._deque.append(val)
        self._seen.add(val)

    def front(self) -> np.ndarray:
        imgpath = self._directory / self._deque[0]
        try:
            return czifile.imread(imgpath)
        except FileNotFoundError:
            print(f"Error accessing file: {self._deque[0]} no longer exists or cannot be accessed.")
            self.dequeue()
            return self.front()

class ImageQueue(BaseQueue):
    def enqueue(self, val: str) -> None:
        if val in self._seen:
            return
        try:
            imgarr = czifile.imread(self._directory / val)
            self._deque.append(imgarr)
            self._seen.add(val)
        except FileNotFoundError:
            print(f"Error accessing file: {val} no longer exists or cannot be accessed.")

    def front(self) -> np.ndarray:
        return self._deque[0] if not self.is_empty() else None