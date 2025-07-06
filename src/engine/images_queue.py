from typing import Callable
from collections import deque
from abc import ABC, abstractmethod
from src.images.image import BaseImage
from pathlib import Path


'''
In practice, using collections.deque is faster due to being implemented in C.
class Node:
    def __init__(self, data: str, next: 'Node' = None):
        self.data = data
        self.next = next

'''

class BaseQueue(ABC):
    def __init__(self, directory: Path, image_factory: Callable, file_format:str = 'CZI', enqueue_existing: bool = False):
        self._directory = directory
        self._deque = deque()
        self._factory = image_factory
        self._format = file_format
        self._seen = set()
        for val in self._directory.iterdir():
            if val.is_file() and val.suffix.lower() == f'.{self._format}'.lower():
                if enqueue_existing:
                    self.enqueue(val)
                else:
                    self._seen.add(val)

    def is_empty(self) -> bool:
        return not self._deque

    def dequeue(self) -> None:
        if not self.is_empty():
            self._deque.popleft()

    def update(self) -> None:
        for val in self._directory.iterdir():
            if val.is_file() and val.suffix.lower() == f'.{self._format}'.lower():
                self.enqueue(val)

    def __len__(self):
        return len(self._deque)

    @abstractmethod
    def enqueue(self, val: str) -> None:
        pass

    @abstractmethod
    def front(self) -> BaseImage | None:
        pass

class LazyQueue(BaseQueue):
    def enqueue(self, val: str) -> None:
        if val in self._seen:
            return
        self._deque.append(val)
        self._seen.add(val)

    def front(self) -> BaseImage | None:
        while not self.is_empty():
            imgpath = self._directory / self._deque[0]
            image = self._factory(imgpath)
            if image.array is not None:
                return image
            self.dequeue()
        return None

class EagerQueue(BaseQueue):
    def enqueue(self, val: str) -> None:
        if val in self._seen:
            return
        imgpath = self._directory / val
        image = self._factory(imgpath)
        if image.array is not None:
            self._deque.append(image)
            self._seen.add(val)

    def front(self) -> BaseImage | None:
        return self._deque[0] if not self.is_empty() else None

