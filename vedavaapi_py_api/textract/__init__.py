import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def setup_app():
  from vedavaapi_py_api.ullekhanam.backend import paths
  logging.info(": Using " + paths.DATADIR)
  from vedavaapi_py_api.ullekhanam.backend.db import get_db
  # Import all book metadata into the IndicDocs database
  paths.init_data_dir()
  get_db(db_name="ullekhanam").import_all(rootdir=paths.DATADIR)
