import re

import sanskrit_data.schema.books
import sanskrit_data.schema.common
from sanskrit_data.db import DbInterface

from textract.docimage import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class BookPortionsInterface(DbInterface):
  """Operations on BookPortion objects in an Db"""
  def list_books(self, pattern=None):
    iter = self.get_no_target_entities()
    matches = [b for b in iter if not pattern or re.search(pattern, b.path)]
    return matches

  def get(self, path):
    book = sanskrit_data.schema.books.BookPortion.from_path(path=path, db_interface=self)
    book_node = sanskrit_data.schema.common.JsonObjectNode.from_details(content=book)
    book_node.fill_descendents(self)
    return book_node

  def update_image_annotations(self, page):
    """return the page annotation with id = anno_id"""
    from os import path
    from ullekhanam.backend import paths
    page_image = DocImage.from_path(path=path.join(paths.DATADIR, page.path))
    known_annotations = page.get_targetting_entities(db_interface=self,
                                                     entity_type=ullekhanam.ImageAnnotation.get_wire_typeid())
    if len(known_annotations):
      logging.warning("Annotations exist. Not detecting and merging.")
      return known_annotations
      # # TODO: fix the below and get segments.
      # #
      # # # Give me all the non-overlapping user-touched segments in this page.
      # for annotation in known_annotations:
      #   target = annotation.targets[0]
      #   if annotation.source.source_type == 'human':
      #     target['score'] = float(1.0)  # Set the max score for user-identified segments
      #   # Prevent image matcher from changing user-identified segments
      #   known_annotation_targets.insert(target)

    # Create segments taking into account known_segments
    detected_regions = page_image.find_text_regions()
    logging.info("Matches = " + str(detected_regions))

    new_annotations = []
    for region in detected_regions:
      del region.score
      target = ullekhanam.ImageTarget.from_details(container_id=page._id, rectangle=region)
      annotation = ullekhanam.ImageAnnotation.from_details(
        targets=[target], source=ullekhanam.AnnotationSource.from_details(source_type='system_inferred', id="pyCV2"))
      annotation = annotation.update_collection(self)
      new_annotations.append(annotation)
    return new_annotations
