from pathlib import Path
import os
from collections import deque
from abc import ABC, abstractmethod
import numpy as np
import czifile
import time


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
    def front(self) -> np.ndarray | None:
        pass

class FileQueue(BaseQueue):
    def enqueue(self, val: str) -> None:
        if val in self._seen:
            return
        self._deque.append(val)
        self._seen.add(val)

    def front(self) -> np.ndarray | None:
        while not self.is_empty():
            imgpath = self._directory / self._deque[0]
            imgarr = stable_read(imgpath)
            if imgarr:
                return imgarr
            else:
                self.dequeue()
        return None

class ImageQueue(BaseQueue):
    def enqueue(self, val: str) -> None:
        if val in self._seen:
            return
        imgpath = self._directory / val
        imgarr = stable_read(imgpath)
        if imgarr:
            self._deque.append(imgarr)
            self._seen.add(val)

    def front(self) -> np.ndarray | None:
        return self._deque[0] if not self.is_empty() else None

def stable_read(img_path: Path, max_attempts: int=10, delay_s:float=0.2, required_stable:int=3) -> np.ndarray | None:
    attempts = 0
    stable_count = 0
    try:
        while attempts <= max_attempts:
            if not img_path.exists():
                return None
            initial_size = img_path.stat().st_size
            time.sleep(delay_s)
            current_size = img_path.stat().st_size
            if initial_size == current_size and current_size > 0:
                stable_count += 1
            else:
                stable_count = 0
            if stable_count >= required_stable:
                break
            attempts += 1
        if attempts > max_attempts:
            return None
        return czifile.imread(img_path)
    except FileNotFoundError:
        print(f"Error accessing file: {img_path} no longer exists or cannot be accessed.")
    return None