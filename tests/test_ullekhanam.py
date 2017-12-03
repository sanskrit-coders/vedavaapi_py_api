# -*- coding: utf-8 -*-
"""
Tests for the ullekhanam API.
"""

from __future__ import absolute_import

import logging

import pytest
from sanskrit_data.schema import common

from vedavaapi_py_api import run

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


@pytest.fixture(scope='module')
def app_fixture(request):
  app = run.app.test_client()
  return app


def test_book_list(app_fixture):
  url = "ullekhanam/v1/dbs/ullekhanam_test/books"
  response = app_fixture.get(url)
  book_nodes = common.JsonObject.make_from_pickledstring(pickle=response.data)
  assert book_nodes.__len__() > 0