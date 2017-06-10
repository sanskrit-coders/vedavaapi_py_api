import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

INDICDOC_DBNAME = "vedavaapi_textract_db"


def setup_app(params, client):
  from textract.backend import paths
  logging.info(": Using " + paths.DATADIR)
  from textract.backend.mongodb import initdb, get_db
  initdb(dbname=INDICDOC_DBNAME, client=client, reset=params.dbreset)

  # Import all book metadata into the IndicDocs database
  paths.init_data_dir(params.reset)
  get_db().importAll(paths.DATADIR)


