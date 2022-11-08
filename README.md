# Git repo automation (Github)

- Do you keep changing the same settings on new repos?
- Is that getting tedious?
- This automated the process!

Automatically add to your repos:

- auto release with autorc

Comming:

- issue templates
- Deployment actions

# Setup

(See `.env.example`)

- Go to https://github.com/settings/organizations
- Switch to your organisation by clicking `Switch to another account` (or use your personal)
- Go to `Developer settings` -> `OAuth Apps` -> `New OAuth App`
- During development, it's OK to set the callback url to: `http://127.0.0.1:5000/githubcallback` and set `GITHUB_OAUTH_REDIRECT_URI` in `.env`
- Copy the `Client ID` into `GITHUB_OAUTH_CLIENT_ID` in `.env` file
- Click `Generate a new client secret` into `GITHUB_OAUTH_CLIENT_SECRET` in `.env` file
- (Most imporant step) Upload an `Application logo`

# Install

```
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

# Run

```
. venv/bin/activate
cd src
python app.asgi
```
## Links

Discovered after writing this: https://github.com/googleapis/github-repo-automation (shows on the right track ?)

https://github.com/googleapis/repo-automation-bots
