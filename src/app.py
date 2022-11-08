import os
import secrets
from quart import Quart, render_template, request, session, url_for, redirect
from dotenv import load_dotenv
from base64 import b64encode
import requests
import json

from quart_schema import (
    QuartSchema,
)

load_dotenv(verbose=True)

GITHUB_OAUTH_CLIENT_ID = os.getenv("GITHUB_OAUTH_CLIENT_ID")
GITHUB_OAUTH_CLIENT_SECRET = os.getenv("GITHUB_OAUTH_CLIENT_SECRET")
GITHUB_OAUTH_REDIRECT_URI = os.getenv("GITHUB_OAUTH_REDIRECT_URI")
REPO_TEMPLATE_DIR = os.getenv("REPO_TEMPLATE_DIR=/usr/src/app/")

app = Quart(__name__)
app.config.from_prefixed_env()
QuartSchema(app)


@app.route("/")
async def index():
    client_id = GITHUB_OAUTH_CLIENT_ID
    state = f"{secrets.token_urlsafe(30)}"
    github_authorize_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&state={state}&scope=repo%20user:email%20workflow"  # noqa: E501

    return await render_template(
        "index.html",
        github_authorize_url=github_authorize_url,
    )


@app.route("/githubcallback/")
async def githubcallback():
    code = request.args.get("code")

    # Get access token by POST'ing to github access token endpoint
    data = {
        "client_id": GITHUB_OAUTH_CLIENT_ID,
        "client_secret": GITHUB_OAUTH_CLIENT_SECRET,
        "code": code,
        "redirect_uri": GITHUB_OAUTH_REDIRECT_URI,
    }
    headers = {"Accept": "application/json"}
    req = requests.post(
        "https://github.com/login/oauth/access_token",
        data=data,
        headers=headers,  # noqa: E501
    )

    # Get access token from github
    resp = req.json()
    access_token = resp.get("access_token")
    session["access_token"] = access_token

    return redirect(url_for("index"))


@app.post("/configure-repo")
async def configure_repo():
    data = await request.get_json()
    org_name = data["org_name"]
    repo_name = data["repo_name"]

    # Use access token to configure repo
    access_token = session.get("access_token")
    headers = {"Authorization": f"token {access_token}"}
    headers["Accept"] = "application/vnd.github+json"
    req = requests.get("https://api.github.com/user", headers=headers).json()

    # Get GitHub username for commit message
    username = req.get("login")
    # Get email address so can do git commits with correct author information
    req = requests.get("https://api.github.com/user/emails", headers=headers)
    email = req.json()[0].get("email", None)

    # Commit autorc repo content
    with open(f"{REPO_TEMPLATE_DIR}/.autorc") as fp:
        autorc = fp.read()
        autorc = autorc.replace("GITHUB_OWNER", username)
        autorc = autorc.replace("GITHUB_REPO_NAME", repo_name)
        autorc_b64 = b64encode(autorc.encode("utf-8")).decode("utf-8")
        data = {
            "message": "create .autorc",
            "committer": {"name": username, "email": email},
            "content": autorc_b64,
        }
        req = requests.put(
            f"https://api.github.com/repos/{org_name}/{repo_name}/contents/.autorc",  # noqa: E501
            headers=headers,
            data=json.dumps(data),
        )

    # Commit ISSUE_TEMPLATE
    with open(
        f"{REPO_TEMPLATE_DIR}/.github/ISSUE_TEMPLATE/feature_request.md"  # noqa: E501
    ) as fp:  # noqa: E501
        issue_template = fp.read()
        issue_template = issue_template.replace("GITHUB_OWNER", username)
        issue_template = issue_template.replace("GITHUB_REPO_NAME", repo_name)
        issue_template_b64 = b64encode(issue_template.encode("utf-8")).decode(
            "utf-8"
        )  # noqa: E501
        data = {
            "message": "create .issue_template",
            "committer": {"name": username, "email": email},
            "content": issue_template_b64,
        }
        req = requests.put(
            f"https://api.github.com/repos/{org_name}/{repo_name}/contents/.github/ISSUE_TEMPLATE/feature_request.md",  # noqa: E501
            headers=headers,
            data=json.dumps(data),
        )

    session["repo_name"] = repo_name
    session["org_name"] = org_name
    session["repo_name_configure_completed"] = repo_name
    return redirect(url_for("index"))
