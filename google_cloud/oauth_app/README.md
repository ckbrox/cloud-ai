# OAuth App
A simple Flask App to get GCP OAuth credentials.

## Get Started

### Install Requirements
`pip install -r requirements.txt`

### Create OAuth Credentials in GCP
https://www.youtube.com/watch?v=1Ua0Eplg75M
1. Enable APIs (i.e. Gmail API)
2. Configure Consent Screen
 - Authorized JavaScript origins
    - http://localhost
    - http://localhost:5000

- Authorized redirect URIs
    - http://localhost:5000/oauth2callback
3. Create credentials: create Web Application credentials and save the client_id/secret JSON file

### Configure Secret Manager
1. Upload your credentials to Google Cloud Secret Manager and replace gcp.py `ckb-google-oauth` with your secret ID
2. Create a secret to store the user's Oauth Credentials (access token, refresh token, etc.). You can create a blank secret but replace gcp.py `ckb-google-oauth-creds` with your secret ID

## Run the Code
`python oauth_app.py`
