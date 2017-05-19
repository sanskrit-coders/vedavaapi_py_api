import logging
import sys

import jsonpickle

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

logging.info("hello")


def main(argv):
    from textract.backend.data_containers import *
    logging.info(jsonpickle.dumps(ImageAnnotation.schema))
    pass


if __name__ == "__main__":
    main(sys.argv[1:])
