class BookPortion:
  def __init__(self, title, authors):
    self.json_type = self.__class__.__name__
    self.title = title
    self.authors = authors

