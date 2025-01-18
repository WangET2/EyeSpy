import numpy as np
import cv2 as cv
import czifile
from pathlib import Path
import statistics as stat
import math
from decimal import Decimal

WHITE_POINT = 4096
KERNEL = np.ones((9,9), np.uint8)

def runprocessing(file: Path) -> float:
    #Initialize image as 2D numpy array.
    czi_file = czifile.CziFile(file)
    cziimg = _reduce_dims(czi_file.asarray())

    #Get image scaling.
    metadata = czi_file.metadata(raw=False)
    scaling = str(metadata['ImageDocument']['Metadata']['Scaling']['Items']['Distance'][0]['Value'])
    scaling = float(scaling[:scaling.index('e')])
    czi_file.close()

    #Apply thresholding.
    bestfit = _best_fit(cziimg)
    thresholded = _threshold_unique(bestfit)
    thresholded_8u = cv.normalize(thresholded, dst=None,
                                  alpha=0, beta=255,
                                  norm_type=cv.NORM_MINMAX, dtype=cv.CV_8U)
    opened = cv.morphologyEx(thresholded_8u, cv.MORPH_OPEN, KERNEL)
    closed = cv.morphologyEx(opened, cv.MORPH_CLOSE, KERNEL)

    #Apply distance transform to remove loosely connected regions.
    regressed = cv.distanceTransform(closed, cv.DIST_L2, 5)

    #Reapply thresholding to create binary mask.
    thresholded2 = _threshold_unique(regressed)
    opened2 = cv.morphologyEx(thresholded2, cv.MORPH_OPEN, KERNEL)
    closed2 = cv.morphologyEx(opened, cv.MORPH_CLOSE, KERNEL)

    #Use contours to remove background fluorescence.
    contours, hierarchy = cv.findContours(closed2, cv.RETR_EXTERNAL,
                                          cv.CHAIN_APPROX_SIMPLE)
    eye = max(contours, key=cv.contourArea)

    #Fit an ellipse to approximate eye shape.
    ellipse = cv.fitEllipse(eye)
    cx, cy = ellipse[0]
    major, minor = ellipse[1]
    theta = ellipse[2]

    #Determine radius of Region of Interest.
    if theta <= 90:
        yrad = (major / 2) * math.sin(math.radians(theta))
        xrad = (major / 2) * math.cos(math.radians(theta))
    elif 90 < theta <= 180:
        yrad = (major / 2) * math.sin(math.radians(180 - theta))
        xrad = (major / 2) * math.cos(math.radians(180 - theta))

    #Ensure Region of Interest is within image bounds.
    y_shape, x_shape = thresholded_8u.shape
    if yrad - cy < 0:
        yrad = cy
    if yrad + cy >= y_shape:
        yrad = y_shape - cy - 1
    if xrad - cx < 0:
        xrad = cx
    if xrad + cx >= x_shape:
        xrad = x_shape - cx - 1
    radius = min(yrad, xrad, 2500/scaling)

    #Determine mean flourescence of ROI.
    roi = []
    for a in range(y_shape):
        for b in range(x_shape):
            if pow(b - cx, 2) + pow(a - cy, 2) <= pow(radius, 2):
                roi.append(float(cziimg[a][b]))

    meanflour = stat.mean(roi)
    rounded = round(Decimal(str(meanflour)), 3)
    return float(rounded)
    


def _reduce_dims(cziarr: 'numpy array') -> 'numpy array':
    a, y, x, b = cziarr.shape
    newarr = np.zeros((y, x), np.uint64)
    for i in range(y):
        for j in range(x):
            newarr[i][j] = cziarr[0][i][j][0]
    return newarr

def _best_fit(cziarr: 'numpy array') -> 'numpy array':
    y, x = cziarr.shape
    newarr = np.zeros((y,x), np.uint64)
    median = np.median(cziarr)
    iqr = np.percentile(cziarr, 75) - np.percentile(cziarr, 25)
    ubound = median + (1.5 * iqr)
    brightest = 0
    for i in range(y):
        for j in range(x):
            if cziarr[i][j] > brightest and cziarr[i][j] <= ubound:
                brightest = cziarr[i][j]
    for a in range(y):
        for b in range(x):
            if cziarr[a][b] > brightest:
                newarr[a][b] = WHITE_POINT
            else:
                newarr[a][b] = (cziarr[a][b] * 4096) / brightest
    return newarr

def _threshold_unique(cziarr: 'array') -> 'np array':
    y, x = cziarr.shape
    uniquevals = np.unique(cziarr)
    lbound = np.percentile(uniquevals, 40)
    newarr = np.zeros((y,x), np.uint8)
    for i in range(y):
        for j in range(x):
            if cziarr[i][j] >= lbound:
                newarr[i][j] = 255
    return newarr
