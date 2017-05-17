import logging
from copy import deepcopy

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def check_class(obj, allowed_types):
  results = [isinstance(obj, some_type) for some_type in allowed_types]
  # logging.debug(results)
  return (True in results)


def check_list_item_types(some_list, allowed_types):
  check_class_results = [check_class(item, allowed_types=allowed_types) for item in some_list]
  # logging.debug(check_class_results)
  return not (False in check_class_results)


def urlize(pathsuffix, text=None, newtab=True):
  tabclause = ""
  if newtab:
    tabclause = 'target="_blank"'
  if not text:
    text = pathsuffix
  return '<a href="/workloads/taillog/15/' + pathsuffix + '" ' + tabclause + '>' + text + '</a>'


def recursively_merge(a, b):
  assert a.__class__ == b.__class__, str(a.__class__) + " vs " + str(b.__class__)

  if isinstance(b, dict) and isinstance(a, dict):
    a_and_b = a.viewkeys() & b.viewkeys()
    every_key = a.viewkeys() | b.viewkeys()
    return {k: recursively_merge(a[k], b[k]) if k in a_and_b else
      deepcopy(a[k] if k in a else b[k]) for k in every_key}
  elif isinstance(b, list) and isinstance(a, list):
    return list(set(a + b))
  else:
    return b
  return deepcopy(b)