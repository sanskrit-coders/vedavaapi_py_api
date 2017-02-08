import cv2
import sys, os
import json 
from operator import itemgetter, attrgetter
from pprint import pprint
from os import path
from docimage import *

img = DocImage(sys.argv[1])
cv2.imshow('Binarized image', img.img_bin)
cv2.waitKey(0)
cv2.destroyAllWindows()
