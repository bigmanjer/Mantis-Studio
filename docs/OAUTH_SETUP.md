# OAuth Setup

MANTIS Studio currently supports Google sign-in through OAuth 2.0 authorization
code flow.

## Google

1. Open Google Cloud Console and create or select a project.
2. Configure the OAuth consent screen.
3. Create an OAuth client of type Web application.
4. Add the exact redirect URI shown in MANTIS User Settings.
   For the hosted Streamlit app this is:

   `https://mantisstudio.streamlit.app/?oauth_provider=google`

   For local Streamlit this is usually:

   `http://localhost:8501/?oauth_provider=google`

   Do not enter only `mantisstudio.streamlit.app`; Google requires the full
   URL, including `https://` and `?oauth_provider=google`.

5. Sign in as the built-in `ADMIN` account.
6. Open `User Settings -> OAuth Sign-In`.
7. Enable Google sign-in and paste:
   - Google Client ID
   - Google Client Secret
   - Redirect URI
   - Scopes: `openid email profile`
8. Save settings.

The client secret is protected locally with Windows DPAPI when running on
Windows. If protected storage is unavailable, MANTIS refuses to persist the
secret instead of writing it as plaintext config.

For hosted deployments such as Streamlit Cloud, store the secret outside the
app config instead:

- Environment variable: `MANTIS_GOOGLE_CLIENT_SECRET`
- Streamlit secret: `google_client_secret`
- Alternate Streamlit secret: `oauth_google_client_secret`

When one of these secure external secrets is present, MANTIS uses it for Google
OAuth and does not need to save the secret from User Settings.

## Account Linking

Google accounts are linked by verified email address. If a matching local
account exists, Google is attached to that account. Otherwise MANTIS creates a
new member account with a hidden account ID.

The built-in `ADMIN` account cannot be claimed through OAuth.

## Troubleshooting

- `Google OAuth missing: redirect URI` means the super admin has not saved a
  redirect URI in User Settings.
- `redirect URI must be a full URL` means the value is missing `http://` or
  `https://`.
- `redirect URI must include ?oauth_provider=google` means MANTIS cannot tell
  that Google sent the user back to the app.
- `redirect_uri_mismatch` from Google means the URI saved in MANTIS and the URI
  in Google Cloud do not match exactly.
- `Protected secret storage is unavailable` means the app cannot safely save the
  secret to local config. Use `MANTIS_GOOGLE_CLIENT_SECRET` or Streamlit
  `google_client_secret` instead.
