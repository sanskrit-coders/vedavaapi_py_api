
import logging

# Essential for depickling to work.
from vedavaapi_data.schema import *  # pylint: disable=unused-import.

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

#Dummy usage.
logging.debug("So that depickling works well, we imported: " + str([common, ullekhanam, books, users]))