import os
from collections import deque
from abc import ABC, abstractmethod
from src.engine.config import Config
from src.images.image import BaseImage, create_image_from_config


'''
In practice, using collections.deque is faster due to being implemented in C.
class Node:
    def __init__(self, data: str, next: 'Node' = None):
        self.data = data
        self.next = next

'''

class BaseQueue(ABC):
    def __init__(self, config: Config, *, enqueue_existing: bool = False):
        self._config = config
        self._directory = config.directory
        self._deque = deque()
        self._seen = set()
        for val in os.listdir(self._directory):
            if config.enqueue_existing | enqueue_existing:
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
            if val.is_file():
                self.enqueue(val.name)

    @abstractmethod
    def enqueue(self, val: str) -> None:
        pass

    @abstractmethod
    def front(self) -> BaseImage | None:
        pass

class FileQueue(BaseQueue):
    def enqueue(self, val: str) -> None:
        if val in self._seen:
            return
        self._deque.append(val)
        self._seen.add(val)

    def front(self) -> BaseImage | None:
        while not self.is_empty():
            imgpath = self._directory / self._deque[0]
            image = create_image_from_config(self._config, imgpath)
            if image.array is not None:
                return image
            self.dequeue()
        return None

class ImageQueue(BaseQueue):
    def enqueue(self, val: str) -> None:
        if val in self._seen:
            return
        imgpath = self._directory / val
        image = create_image_from_config(self._config, imgpath)
        if image.array is not None:
            self._deque.append(image)
            self._seen.add(val)

    def front(self) -> BaseImage | None:
        return self._deque[0] if not self.is_empty() else None

def create_queue_from_config(config: Config, *, enqueue_existing = False):
    if config.queue_type == 'Image':
        return ImageQueue(config, enqueue_existing=enqueue_existing)
    return FileQueue(config, enqueue_existing=enqueue_existing)