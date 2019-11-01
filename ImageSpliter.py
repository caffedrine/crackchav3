#!/usr/bin/python3
from PIL import ImageFile
import sys
import logging
import os
import glob
import re

from natsort import natsorted

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def ImgSplit(imgPath):
    outputPath = os.path.dirname(imgPath)
    with open(imgPath, "rb") as fd:
        p = ImageFile.Parser()
        p.feed(fd.read())
        image = p.close()

        img2 = image.copy()
        w, h = image.size

        ranges = []
        start = 0

        for x in range(0, w):
            is_empty = True
            for y in range(0, h):
                if image.getpixel((x, y)) == BLACK:
                    is_empty = False
                    break

            if is_empty:
                if start < x - 1:
                    ranges.append((start, x - 1))
                start = x + 1

        ranges.append((start, w - 1))
        logging.debug(ranges)

        for i, (range_start, range_end) in enumerate(ranges):
            # print("Processing range {}-{}".format(range_start, range_end))
            y_start = 0xFFFF
            y_end = 0

            for y in range(h):
                for x in range(range_start, range_end):
                    if image.getpixel((x, y)) == BLACK:
                        y_start = min(y, y_start)
                        y_end = max(y, y_end)

            img2 = image.crop(box=(range_start, y_start, min(range_end + 1, w), y_end + 1))
            j = 0
            while True:
                filename = outputPath + "/{}.png".format(i)

                img2.save(filename)
                break
    return True
