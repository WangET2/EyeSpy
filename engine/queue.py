from pathlib import Path
import os

class Node:
    def __init__(self, data: str, next: 'Node' = None):
        self.data = data
        self.next = next

class FileQueue:
    def __init__(self, directory: Path, *, enqueue_existing=False):
        self._directory = directory
        self._head = None
        self._tail = None
        self._seen = set()
        for val in os.listdir(directory):
            if enqueue_existing:
                self.enqueue(val)
            else:
                self._seen.add(val)

    def is_empty(self) -> bool:
        return self._head is None

    def enqueue(self, val: str) -> None:
        if val in self._seen:
            return
        if self.is_empty():
            self._head = Node(val)
            self._tail = self._head
        else:
            self._tail.next = Node(val)
            self._tail = self._tail.next
        self._seen.add(val)

    def front(self) -> Path:
        if self.is_empty():
            return None
        return self._directory / self._head.data

    def dequeue(self) -> None:
        if self.is_empty():
            return
        self._head = self._head.next
        if self.is_empty():
            self._tail = None

    def update(self) -> None:
        for val in self._directory.iterdir():
            if val.is_file():
                self.enqueue(val.name)
