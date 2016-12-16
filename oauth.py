from rauth import OAuth1Service, OAuth2Service
from flask import current_app, url_for, request, redirect, session
import json
import re


class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', provider=self.provider_name,
                       _external=True)

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class FacebookSignIn(OAuthSignIn):
    def __init__(self):
        super(FacebookSignIn, self).__init__('facebook')
        self.service = OAuth2Service(
            name='facebook',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://graph.facebook.com/oauth/authorize',
            access_token_url='https://graph.facebook.com/oauth/access_token',
            base_url='https://graph.facebook.com/'
        )

    def authorize(self):
        print "Call-backUrl=",self.get_callback_url()
        ips = re.findall( r'[0-9]+(?:\.[0-9]+){3}',self.get_callback_url())
        callback_url=None
        if not self.get_callback_url().__contains__("vedavaapi.org"):
            callback_url = self.get_callback_url().replace(ips[0],"vedavaapi.org")
        else:
            callback_url=self.get_callback_url()
        print "callback_url_final=",callback_url

        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=callback_url)
        )

    def callback(self):
        if 'code' not in request.args:
            return None, None, None, 0
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()}
        )
        onlyname= oauth_session.get('me').json()['name']
        print "only-name=",onlyname
        me = oauth_session.get('me?fields=id,email').json()
        #print "phone-number=",json.dumps(me,indent=4)
        if me.get('email')==None:
            return ('facebook' + me['id'], onlyname, me.get('email'),1)
        else:
            return (
                'facebook$' + me['id'],
                #onlyname,
                me.get('email').split('@')[0], #for getting username from email
                me.get('email'),
                1
            )


class TwitterSignIn(OAuthSignIn):
    def __init__(self):
        super(TwitterSignIn, self).__init__('twitter')
        self.service = OAuth1Service(
            name='twitter',
            consumer_key=self.consumer_id,
            consumer_secret=self.consumer_secret,
            request_token_url='https://api.twitter.com/oauth/request_token',
            authorize_url='https://api.twitter.com/oauth/authorize',
            access_token_url='https://api.twitter.com/oauth/access_token',
            base_url='https://api.twitter.com/1.1/'
        )

    def authorize(self):
        request_token = self.service.get_request_token(
            params={'oauth_callback': self.get_callback_url()}
        )
        session['request_token'] = request_token
        return redirect(self.service.get_authorize_url(request_token[0]))

    def callback(self):
        request_token = session.pop('request_token')
        if 'oauth_verifier' not in request.args:
            return None, None, None, 0
        oauth_session = self.service.get_auth_session(
            request_token[0],
            request_token[1],
            data={'oauth_verifier': request.args['oauth_verifier']}
        )
        me = oauth_session.get('account/verify_credentials.json').json()
        social_id = 'twitter$' + str(me.get('id'))
        username = me.get('screen_name')
        return social_id, username, None, 1   # Twitter does not provide email


