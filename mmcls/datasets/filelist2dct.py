from io import BytesIO

import numpy as np
from jpeg2dct.numpy import loads as dct_loads
from PIL import Image


def convertToJpeg(im):
    with BytesIO() as f:
        im.save(f, format='JPEG')
        return f.getvalue()

def getDCT(jpg_img):
    dct_y, dct_cb, dct_cr = dct_loads(jpg_img)
    return dct_y, dct_cb, dct_cr


def get_dct_from_imgpath(img_path):
    img = Image.open(img_path).convert('RGB')
    img_dct = getDCT(convertToJpeg(img))
    return img, img_dct


if __name__ == '__main__':
    img_path = "/data/laserclassification/extracted/day_split/val/day2/IMG_5281.png"
    img_path = "/data/laserclassification/extracted/day_split/val/day4/IMG_4448.JPEG"
    img, img_dct = get_dct_from_imgpath(img_path)
    print(np.array(img).shape)
    print(np.array(img_dct[0]).shape, np.array(img_dct[1]).shape, np.array(img_dct[2]).shape)
