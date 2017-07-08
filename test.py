import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

logging.info("hello")


def main(argv):
    from vedavaapi_data.schema.ullekhanam import *
    logging.info(jsonpickle.dumps(ImageAnnotation.schema))
    pass


if __name__ == "__main__":
    main(sys.argv[1:])
