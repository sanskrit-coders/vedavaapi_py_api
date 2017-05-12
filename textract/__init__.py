import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

INDICDOC_DBNAME = "vedavaapi_db"


def setup_app(params):
  from textract.backend import paths
  logging.info(": Using " + paths.DATADIR)
  from textract.backend.db import initdb, get_db
  initdb(INDICDOC_DBNAME, params.dbreset)

  # Import all book metadata into the IndicDocs database
  paths.init_data_dir(params.reset)
  get_db().importAll(paths.DATADIR)


