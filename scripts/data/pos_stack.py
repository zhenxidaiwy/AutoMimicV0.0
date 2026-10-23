"""Stack several contact sheets vertically into one image with a filename label (for faster review).

Usage: python -I pos_stack.py <out.png> <sheet.png> [<sheet.png> ...]
"""
import os
import sys

import cv2
import numpy as np

if __name__ == "__main__":
    ims = []
    for p in sys.argv[2:]:
        im = cv2.imread(p)
        if im is None:
            continue
        lab = np.zeros((18, im.shape[1], 3), np.uint8)
        cv2.putText(lab, os.path.basename(p), (3, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        ims.append(np.concatenate([lab, im], 0))
    w = max(i.shape[1] for i in ims)
    ims = [cv2.copyMakeBorder(i, 0, 0, 0, w - i.shape[1], cv2.BORDER_CONSTANT) for i in ims]
    cv2.imwrite(sys.argv[1], np.concatenate(ims, 0))
