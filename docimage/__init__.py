import cv2
import numpy as np
import preprocessing
import sys
import json
from operator import itemgetter, attrgetter
from pprint import pprint


class DotDict(dict):
    def __getattr__(self, name):
        return self[name] if name in self else None
    def __setattr__(self, name, value):
        self[name] = value

# Represents a rectangular image segment
class ImgSegment(DotDict):
    # Two segments are 'equal' if they overlap
    def __eq__(self, other):
        xmax = max(self.x, other.x)
        ymax = max(self.y, other.y)
        w = min(self.x+self.w, other.x+other.w) - xmax
        h = min(self.y+self.h, other.y+other.h) - ymax
        return w > 0 and h > 0

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if self == other:
            print str(self) + " overlaps " + str(other)
            return 0
        elif (self.y < other.y) or ((self.y == other.y) and (self.x < other.x)):
            return -1
        else:
            return 1
    def __str__(self):
        mystr = "(" + \
            ", ".join(map(lambda p: json.dumps(self[p]) if p in self else "", \
                            ["x", "y", "w", "h", "score", "state", "text"])) \
            + ")"
        return mystr.encode('utf-8')

class DisjointSegments:
    segments = []

    def __init__(self, segments = []):
        self.segments = []
        self.merge(segments)

    def to_rect(self, seg):
        return DotDict(seg)

    def intersection(self, a, b):
        x = max(a.x, b.x)
        y = max(a.y, b.y)
        w = min(a.x+a.w, b.x+b.w) - x
        h = min(a.y+a.h, b.y+b.h) - y
        return w > 0 and h > 0
        #if w<=0 or h<=0: return () # or (0,0,0,0) ?
        #return (x, y, w, h)

    def overlap(self, testseg):
        #testrect = self.to_rect(testseg)
        for i in range(len(self.segments)):
            if self.segments[i] == testseg:
                return i
        return -1

    def insert(self, newseg):
        #print "Inserting " + str(newseg)
        i = self.overlap(newseg)
        if i >= 0:
            if self.segments[i].score >= newseg.score:
                #print "Skipping " + str(newseg) + " < " + str(self.segments[i])
                return False
            else:
                self.remove(i)
                #for r in self.segments:
                #    print "->  " + str(r)
        #print "--> at " + str(len(self.segments))
        self.segments.append(newseg)
        return True

    def merge(self, segments):
        merged = [r for r in segments if self.insert(r)]
        return merged

    def get(self, i):
        return self.segments[i] if i >= 0 and i < len(self.segments) else None

    def remove(self, i):
        #print "deleting " + str(i) + "(" + str(len(self.segments)) + "): " + str(self.segments[i])
        if i >= 0 and i < len(self.segments):
            del self.segments[i]

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

    def find_matches(self, template_img, thres = 0.7, known_segments = None):
        res = cv2.matchTemplate(self.img_bin,  template_img.img_bin, cv2.TM_CCOEFF_NORMED )
   
        loc = np.where(res >= float(thres))
        matches = [ImgSegment({ 'x' : pt[0], 'y' : pt[1], \
                        'w' : template_img.w, 'h' : template_img.h, \
                        'score' : float("{0:.2f}".format(res[pt[1], pt[0]])) \
                        }) \
                    for pt in zip(*loc[::-1])]

        if known_segments is None:
            known_segments = DisjointSegments()
        disjoint_matches = known_segments.merge(matches)
        known_segments.segments.sort()
        #for r in known_segments.segments:
        #   print str(r)
        return disjoint_matches

    def find_recurrence(self, r, thres = 0.7, known_segments = None):
        #print "Searching for recurrence of " + json.dumps(r)

        template_img = self.img_rgb[r.y:(r.y+r.h), r.x:(r.x+r.w)]
        template = DocImage()
        template.fromImage(template_img)

        if known_segments is None:
            known_segments = DisjointSegments()
        known_segments.insert(ImgSegment(r))
        return self.find_matches(template, thres, known_segments)

    def annotate(self, sel_areas, color = (0,0,255)):
        for rect in sel_areas:
            cv2.rectangle(self.img_rgb, (rect['x'], rect['y']), \
                (rect['x'] + rect['w'], rect['y'] + rect['h']), color, 2)

def main(args):
    img = DocImage(args[0])
    rect = DotDict({ 'x' : int(args[1]), \
             'y' : int(args[2]), \
             'w' : int(args[3]), 'h' : int(args[4]), 'score' : float(1.0) })
    print "Template rect = " + json.dumps(rect)
    matches = img.find_recurrence(rect, 0.7)
    pprint(matches)
    print "Total", len(matches), "matches found."

    #print json.dumps(matches)
    img.annotate(matches)
    img.annotate([rect], (0,255,0))
    cv2.namedWindow('Annotated image', cv2.WINDOW_NORMAL)
    cv2.imshow('Annotated image', img.img_rgb)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])
