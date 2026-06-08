# OAuth Setup

MANTIS Studio currently supports Google sign-in through OAuth 2.0 authorization
code flow.

## Google

1. Open Google Cloud Console and create or select a project.
2. Configure the OAuth consent screen.
3. Create an OAuth client of type Web application.
4. Add the exact redirect URI shown in MANTIS User Settings.
   For the hosted Streamlit app this is:

   `https://mantis-studio.streamlit.app/?oauth_provider=google`

   For local Streamlit this is usually:

   `http://localhost:8501/?oauth_provider=google`

   Do not enter only `mantis-studio.streamlit.app`; Google requires the full
   URL, including `https://` and `?oauth_provider=google`.

5. Add the Google client secret to deployment secrets.
6. Restart or redeploy the app.

The client secret is protected locally with Windows DPAPI when running on
Windows. If protected storage is unavailable, MANTIS refuses to persist the
secret instead of writing it as plaintext config.

Google OAuth is deployment-configured. There is no Super Admin menu for client
secrets because hosted apps must not save secrets through the UI.

The public Google client ID and hosted redirect URI are app defaults. For hosted
deployments such as Streamlit Cloud, store the client secret outside the app
config:

- Environment variable: `MANTIS_GOOGLE_CLIENT_SECRET`
- Streamlit secret: `MANTIS_GOOGLE_CLIENT_SECRET`
- Streamlit secret: `google_client_secret`
- Alternate Streamlit secret: `oauth_google_client_secret`

Optional overrides are still available for alternate deployments:

- Environment variable: `MANTIS_GOOGLE_CLIENT_ID`
- Streamlit secret: `MANTIS_GOOGLE_CLIENT_ID`
- Streamlit secret: `google_client_id`
- Optional environment variable: `MANTIS_GOOGLE_REDIRECT_URI`
- Optional Streamlit secret: `MANTIS_GOOGLE_REDIRECT_URI`
- Optional Streamlit secret: `google_redirect_uri`

When these external values are present, MANTIS uses them for Google OAuth. If no
redirect URI is saved, MANTIS defaults to
`https://mantis-studio.streamlit.app/?oauth_provider=google`.

## Account Linking

Google accounts are linked by verified email address. If a matching local
account exists, Google is attached to that account. Otherwise MANTIS creates a
new member account with a hidden account ID.

The built-in `ADMIN` account cannot be claimed through OAuth.

## Troubleshooting

- `Google OAuth missing: redirect URI` means no saved or external redirect URI
  was available. Hosted builds default to the Streamlit callback URL above.
- `redirect URI must be a full URL` means the value is missing `http://` or
  `https://`.
- `redirect URI must include ?oauth_provider=google` means MANTIS cannot tell
  that Google sent the user back to the app.
- `redirect_uri_mismatch` from Google means the URI saved in MANTIS and the URI
  in Google Cloud do not match exactly.
- `Protected secret storage is unavailable` means the app cannot safely save the
  secret to local config. Use `MANTIS_GOOGLE_CLIENT_SECRET` or Streamlit
  `google_client_secret` instead.
