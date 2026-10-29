# Security

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's private reporting
(Security tab > "Report a vulnerability") on this repository. Expect a first answer within 7 days.

Only the `main` branch is supported.

## Known limitations of the current code

MistralTune is a development project. Do not expose it to the internet as is.

| Area | Current behaviour | What to do before any shared deployment |
|------|-------------------|------------------------------------------|
| Authentication | `/api/auth/login` and `/api/auth/register` exist, but the dataset, job and inference endpoints do not require a token. Anyone who reaches the API can upload data, start paid Mistral jobs and cancel them. | Put the API behind a private network or an authenticating proxy. |
| JWT secret | `JWT_SECRET_KEY` falls back to the public string `your-secret-key-change-in-production` (`src/auth/jwt.py`). Tokens signed with it can be forged. | Always set `JWT_SECRET_KEY` to a long random value. |
| CORS | `allow_origins=["*"]` with `allow_credentials=True` (`src/api/main.py`). | Replace `*` with the frontend origin(s). |
| Uploads | With #4: `.jsonl` only, 100 MB cap, stored under a server-generated uuid name. Without it the client file name is used in the storage path. Content is validated line by line, not scanned. | Keep the cap; do not serve the upload directory. |
| Mistral API key | Read from `MISTRAL_API_KEY`. Without it the API logs a warning and uses a mock client. | Keep the key in `.env` (git-ignored) or a secret store, never in the repo. |
