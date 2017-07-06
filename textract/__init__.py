import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

INDICDOC_DBNAME = "vedavaapi_textract_db"


def setup_app(params, client):
  from textract.backend import paths
  logging.info(": Using " + paths.DATADIR)
  from textract.backend.db import get_db
  from textract.backend.db import initdb
  initdb(dbname=INDICDOC_DBNAME, client=client)

  # Import all book metadata into the IndicDocs database
  paths.init_data_dir(params.reset)
  get_db().importAll(paths.DATADIR)


