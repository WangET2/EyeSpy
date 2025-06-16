from modules.filehandler import *
from pathlib import Path
import time
import os
import tracemalloc

DIRECTORY = Path(r'C:\Users\Ethan W\Desktop\newattempt\inputs')

def run():

    image_list = os.listdir(DIRECTORY)
    length = len(image_list)
    length = 10
    a = time.time()
    tracemalloc.start()
    for i in range(length):
        a1 = runprocessing(DIRECTORY / image_list[i])
        print(f"{i + 1}/{length} complete")
    _, peak1 = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    b = time.time()
    old_runtime = (b - a)/length
    print("Old Done")

    c = time.time()
    tracemalloc.start()
    for j in range(length):
        img = CziFlyImage(DIRECTORY / image_list[j])
        b1 = get_contour(img, 100, 100)
        b2 = get_mean_circular(img, b1)
        print(f"{j + 1}/{length} complete")
    _, peak2 = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    d = time.time()
    new_runtime = (d - c)/length

    print(f"Old Runtime: {old_runtime:.4f} sec/image")
    print(f"New Runtime: {new_runtime:.4f} sec/image")
    print(f"Old Memory peak: {peak1 / 1024 ** 2:.2f} MB")
    print(f"New Memory peak: {peak2 / 1024 ** 2:.2f} MB")

if __name__  == '__main__':
    run()