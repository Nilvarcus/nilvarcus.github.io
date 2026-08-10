# Portfolio YouTube stats updater

Run from the repository root:

```bash
python scripts/update_stats.py
```

The updater uses the same read-only Google scopes and OAuth client configuration
as the YouTube Dashboard project. It fetches channel and video data through the
YouTube Data API v3 and private period/audience data through the YouTube
Analytics API, then writes the reviewable public-output file at `stats.json`.

## Local credentials

- The updater first looks for the dashboard OAuth client configuration at
  `%APPDATA%/com.nilvarcus.youtube-dashboard/youtube-oauth-client.json`.
- Override that path with `YOUTUBE_OAUTH_CLIENT_FILE` if needed.
- The first run may open a browser for OAuth consent.
- The updater token is stored outside this repository at
  `%LOCALAPPDATA%/nilvarcus-portfolio/youtube-stats-token.json`.
- Override the token path with `YOUTUBE_STATS_TOKEN_FILE` if needed.
- Never commit client secrets, refresh tokens, access tokens, or credential JSON.

Install dependencies once if necessary:

```bash
python -m pip install -r scripts/requirements.txt
```

`stats.json` intentionally includes review metadata so the numbers can be
checked before using them in the portfolio. The `manual` section is for facts
YouTube cannot provide, such as years of gaming experience and games covered.
