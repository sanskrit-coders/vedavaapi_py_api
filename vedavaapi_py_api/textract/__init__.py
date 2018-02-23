"""
Intro
=====

This is a web-based tool (based on the ullekhanam module) to rapidly
decode scanned Indic document images into searchable text.

-  It will enable users to identify and annotate characters in scanned
   document images and auto-identifies similar characters.

"""

import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)
