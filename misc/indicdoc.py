import cv2
import numpy as np
import preprocessing

class DocImage:
    fname = ""
    img_rgb = None
    img_gray = None
    w = 0
    h = 0

    def load(self, imgfile):
        self.fname = imgfile
        self.img_rgb = cv2.imread(self.fname)
        self.init()

    def init(self):
        self.img_gray = cv2.cvtColor(self.img_rgb, cv2.COLOR_BGR2GRAY)
        self.img_bin = preprocessing.binary_img(self.img_gray)
        self.w, self.h = self.img_gray.shape[::-1]

    def set(img_cv):
        self.img_rgb = img_cv
        self.init()

    def save(self, dstfile):
        cv2.imwrite(dstfile, self.img_rgb)

    def find(self, template_img, thres = 0.7):
        res = cv2.matchTemplate(self.img_bin,  template_img.img_bin, cv2.TM_CCOEFF_NORMED )
   
        loc = np.where(res >= float(thres))

        matches = []
        for pt in zip( *loc[::-1] ):
            matchrect = { 'x' : pt[0], 'y' : pt[1], 'w' : template_img.w, 'h' : template_img.h };
            matches.append(matchrect);
        return matches

    def find_recurrence(self, rect, thres = 0.7):
        template = IndicDoc()
        template.set(img_rgb[rect.y:(rect.y+rect.h), rect.x:(rect.x+rect.w)])
        return self.find_matches(template, thres)

    def annotate(self, sel_areas):
        for rect in sel_areas:
            cv2.rectangle(self.img_rgb, (rect['x'], rect['y']), \
                (rect['x'] + rect['w'], rect['y'] + rect['h']), (0,0,255), 2)
