import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

def setup_app(db):
  from ullekhanam.backend import paths
  logging.info(": Using " + paths.DATADIR)
  from ullekhanam.backend.db import get_db
  from ullekhanam.backend.db import initdb
  initdb(db=db)

  # Import all book metadata into the IndicDocs database
  paths.init_data_dir()
  get_db().importAll(paths.DATADIR)


