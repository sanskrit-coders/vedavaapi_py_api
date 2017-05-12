import logging

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
