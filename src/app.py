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
REPO_TEMPLATE_DIR = os.getenv("REPO_TEMPLATE_DIR")

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
        repos=session.get("repos"),
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

    # Use access token to configure repo
    access_token = session.get("access_token")
    headers = {"Authorization": f"token {access_token}"}
    headers["Accept"] = "application/vnd.github+json"
    session["github_headers"] = headers
    req = requests.get("https://api.github.com/user", headers=headers).json()

    # Get GitHub username for commit message
    username = req.get("login")
    session["username"] = username
    # Get email address so can do git commits with correct author information
    req = requests.get("https://api.github.com/user/emails", headers=headers)
    email = req.json()[0].get("email", None)
    session["email"] = email

    # Get user repos
    req = requests.get(
        f"https://api.github.com/users/{username}/repos?type=all&per_page=100",
        headers=session.get("github_headers"),
    )

    users_repos = req.json()

    # Check if there are more pages of results
    while "next" in req.links.keys():
        # Retrieve the next page of results
        req = requests.get(req.links["next"]["url"], headers=headers)
        users_repos.extend(req.json())

    repos = []
    count = 0
    try:
        for user_repo in users_repos:
            print(f"adding {user_repo}")
            count += count
            repo = user_repo["html_url"].replace("https://github.com/", "")
            repos.append(repo)
    except Exception as e:
        print(e)
        breakpoint()
        print("here")

    session["repos"] = repos

    # Get authenticated users organisation names
    req = requests.get(
        "https://api.github.com/user/orgs",
        headers=session.get("github_headers"),  # noqa: E501
    )
    session["user_orgs"] = req.json()

    return redirect(url_for("index"))


@app.post("/configure-repo")
async def configure_repo():
    data = await request.get_json()
    org_name = data["org_name"]
    repo_name = data["repo_name"]

    session["repo_name"] = repo_name
    session["org_name"] = org_name
    username = session.get("username")
    email = session.get("email")
    headers = session.get("github_headers")

    # Commit autorc repo content
    with open(f"{REPO_TEMPLATE_DIR}/.autorc") as fp:
        autorc = fp.read()
        autorc = autorc.replace("GITHUB_OWNER", org_name)
        autorc = autorc.replace("GITHUB_REPO_NAME", repo_name)
        autorc = autorc.replace("GITHUB_REPO_OWNER_EMAIL", email)
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
        print(req.text)
    with open(f"{REPO_TEMPLATE_DIR}/.github/workflows/release.yml") as fp:
        autorc_release = fp.read()
        autorc_release_b64 = b64encode(autorc_release.encode("utf-8")).decode(
            "utf-8"
        )  # noqa: E501
        data = {
            "message": "create autorc release.yml workflow",
            "committer": {"name": username, "email": email},
            "content": autorc_release_b64,
        }
        req = requests.put(
            f"https://api.github.com/repos/{org_name}/{repo_name}/contents/.github/workflows/release.yml",  # noqa: E501
            headers=headers,
            data=json.dumps(data),
        )
        print(req.text)

    # Commit deploy.yml
    with open(f"{REPO_TEMPLATE_DIR}/.github/workflows/deploy.yml") as fp:
        deploy = fp.read()
        deploy_b64 = b64encode(deploy.encode("utf-8")).decode("utf-8")  # noqa: E501
        data = {
            "message": "create deploy.yml workflow",
            "committer": {"name": username, "email": email},
            "content": deploy_b64,
        }
        req = requests.put(
            f"https://api.github.com/repos/{org_name}/{repo_name}/contents/.github/workflows/deploy.yml",  # noqa: E501
            headers=headers,
            data=json.dumps(data),
        )
        print(req.text)

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
        print(req.text)

    session["repo_name_configure_completed"] = repo_name
    return redirect(url_for("index"))
