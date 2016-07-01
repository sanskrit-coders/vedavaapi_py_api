import cv2
import numpy as np
import preprocessing
import sys
import json

class DotDict(dict):
    def __getattr__(self, name):
        return self[name]

class DisjointSegments:
    segments = []

    def to_rect(self, seg):
        return DotDict(seg)

    def intersection(self, a,b):
        x = max(a.x, b.x)
        y = max(a.y, b.y)
        w = min(a.x+a.w, b.x+b.w) - x
        h = min(a.y+a.h, b.y+b.h) - y
        return w > 0 and h > 0
        #if w<=0 or h<=0: return () # or (0,0,0,0) ?
        #return (x, y, w, h)

    def overlap(self, testseg):
        testrect = self.to_rect(testseg)
        for r in self.segments:
            if self.intersection(r, testrect):
                return True
        return False

    def insert(self, newseg):
        if not self.overlap(newseg):
            self.segments.append(self.to_rect(newseg))
            return True
        return False

    def __init__(self, segments = []):
        self.segments = []
        for r in segments:
            self.insert(r)

class DocImage:
    fname = ""
    img_rgb = None
    img_gray = None
    w = 0
    h = 0

    def __init__(self, imgfile = None):
        if imgfile:
            #print "DocImage: loading ", imgfile
            self.fromFile(imgfile)

    def fromFile(self, imgfile):
        self.fname = imgfile
        self.img_rgb = cv2.imread(self.fname)
        self.init()

    def init(self):
        self.img_gray = cv2.cvtColor(self.img_rgb, cv2.COLOR_BGR2GRAY)
        self.img_bin = preprocessing.binary_img(self.img_gray)
        self.w, self.h = self.img_gray.shape[::-1]
        #print "width = " + str(self.w) + ", ht = " + str(self.h)

    def fromImage(self, img_cv):
        self.img_rgb = img_cv
        self.init()

    def save(self, dstfile):
        cv2.imwrite(dstfile, self.img_rgb)

    def find_matches(self, template_img, thres = 0.7, excl_segments = None):
        res = cv2.matchTemplate(self.img_bin,  template_img.img_bin, cv2.TM_CCOEFF_NORMED )
   
        loc = np.where(res >= float(thres))

        matches = []
        for pt in zip( *loc[::-1] ):
            matchrect = { 'x' : pt[0], 'y' : pt[1], 'w' : template_img.w, 'h' : template_img.h }
            if excl_segments == None or excl_segments.insert(matchrect):
                matches.append(matchrect);
        #print json.dumps(matches)
        return matches

    def find_recurrence(self, r, thres = 0.7, excl_segments = None):
        r = DotDict(r)
        #print "Searching for recurrence of " + json.dumps(r)
        template = DocImage()
        template_img = self.img_rgb[r.y:(r.y+r.h), r.x:(r.x+r.w)]
        template.fromImage(template_img)
        if excl_segments is None:
            excl_segments = DisjointSegments()
        excl_segments.insert(r)
        return self.find_matches(template, thres, excl_segments)

    def annotate(self, sel_areas):
        for rect in sel_areas:
            cv2.rectangle(self.img_rgb, (rect['x'], rect['y']), \
                (rect['x'] + rect['w'], rect['y'] + rect['h']), (0,0,255), 2)

def main(args):
    img = DocImage(args[0])
    rect = { 'x' : int(args[1]), \
             'y' : int(args[2]), \
             'w' : int(args[3]), 'h' : int(args[4]) }
    print "Template rect = " + json.dumps(rect)
    matches = img.find_recurrence(rect, 0.6)
    print json.dumps(matches)
    img.annotate(matches)
    cv2.namedWindow('Annotated image', cv2.WINDOW_NORMAL)
    cv2.imshow('Annotated image', img.img_rgb)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])
