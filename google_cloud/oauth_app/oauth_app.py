import os
import requests
from flask import Flask, redirect, session, request, url_for, render_template_string
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import google.auth.transport.requests
import googleapiclient.discovery
from gcp import GoogleCloudService

service = GoogleCloudService()

app = Flask(__name__)
app.secret_key = os.urandom(24)


credentials_config = service.oauth_credentials

# Set up the OAuth 2.0 flow
flow = Flow.from_client_config(
    client_config={'web': credentials_config},
    scopes=['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/gmail.readonly', 'openid'],
    redirect_uri='http://localhost:5000/oauth2callback'
)

@app.route('/')
def index():
    if 'credentials' not in session:
        return '<a href="/authorize">Authorize with Google</a>'

    credentials = Credentials(**session['credentials'])
    gmail = googleapiclient.discovery.build('gmail', 'v1', credentials=credentials)
    user_info = gmail.users().getProfile(userId='me').execute()
    return f'Hello {user_info["emailAddress"]}! <a href="/revoke">Revoke</a> <a href="/clear">Clear</a>'

@app.route('/authorize')
def authorize():
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = request.args.get('state')
    if state != session['state']:
        return 'Invalid state parameter.'

    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    service.update_oauth_credentials(session['credentials'])

    return redirect(url_for('index'))

@app.route('/revoke')
def revoke():
    if 'credentials' not in session:
        return 'You are not authorized.'

    credentials = Credentials(**session['credentials'])
    requests.post('https://oauth2.googleapis.com/revoke',
        params={'token': credentials.token},
        headers = {'content-type': 'application/x-www-form-urlencoded'})

    session.clear()
    return 'Token revoked.'

@app.route('/clear')
def clear():
    session.clear()
    return 'Session cleared.'

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True)