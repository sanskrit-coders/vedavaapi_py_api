from docimage import *

img = DocImage(sys.argv[1])
cv2.imshow('Binarized image', img.img_bin)
cv2.waitKey(0)
cv2.destroyAllWindows()
