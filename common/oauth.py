from flask import url_for, session
from flask_oauthlib.client import OAuth
import logging
logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

from vedavaapi_data.schema.common import User

class OAuthSignIn():
  """An interface to be extended for supporting various oauth authentication providers.
  
  Important private members:
    provider_name
    service: An oauth.remote_app object, set in the subclass constructor.
  """

  providers = None

  def __init__(self, provider_name):
    self.provider_name = provider_name

  # User-agent is directed to the oauth provider website, with a standard callback url.
  def authorize(self):
    callback_url = url_for('.authorized', provider=self.provider_name,
            _external=True)
    return self.service.authorize(callback_url)

  def authorized_response(self):
    return self.service.authorized_response()

  @classmethod
  def get_provider(self, provider_name):
    if self.providers is None:
      self.providers = {}
      for provider_class in self.__subclasses__():
        provider = provider_class()
        self.providers[provider.provider_name] = provider
    return self.providers[provider_name]

  @staticmethod
  def get_token(token=None):
    return session.get('oauth_token')

  def get_session_data(self, data):
    pass

  # Use oauth token in session to get userdata from the oauth service
  def get_user_data(self):
    return None


class GoogleSignIn(OAuthSignIn):
  def __init__(self, client_id, client_secret):
    super(GoogleSignIn, self).__init__(provider_name="google")
    oauth = OAuth()
    self.service = oauth.remote_app(
      'google',
      consumer_key=client_id,
      consumer_secret=client_secret,
      request_token_params={
        'scope': 'email'
      },
      base_url='https://www.googleapis.com/oauth2/v1/',
      request_token_url=None,
      access_token_method='POST',
      access_token_url='https://accounts.google.com/o/oauth2/token',
      authorize_url='https://accounts.google.com/o/oauth2/auth',
    )
    self.service.tokengetter(GoogleSignIn.get_token)

  def get_session_data(self, data):
    return (
      data['access_token'],
      ''
    )

  def get_user_data(self):
    access_token = session.get('oauth_token')
    token = 'OAuth ' + access_token[0]
    headers = {b'Authorization': bytes(token.encode('utf-8'))}
    data = self.service.get(
      'https://www.googleapis.com/oauth2/v1/userinfo', None,
      headers=headers)
    return data.data

  def get_user(self):
    data = self.get_user_data()
    from common.db.user_db import user_db
    user_db = user_db.get_db()
    user = user_db.find_one(filter={"user_id": data['email'], "auth_provider": self.provider_name})
    logging.debug(user)
    if user is None:
      user = User.from_details(nickname=data['name'], user_id=data['email'], auth_provider=self.provider_name)
      logging.debug(user)

    from flask_login import login_user
    login_user(user)
    return url_for('/')
