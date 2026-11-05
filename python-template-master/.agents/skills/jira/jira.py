#!/usr/bin/env python3
"""Small Jira Cloud client for the jira skill. Standard library only.

Reads the project config `.claude/jira.json` (found by walking up from the
current directory) and the API token from the env file it names. Talks to the
gateway `api.atlassian.com/ex/jira/<cloud_id>`, which accepts both scoped and
classic tokens. Uses REST API v2 so descriptions and comments are Jira wiki
markup strings rather than Atlassian Document Format JSON.

    jira.py whoami
    jira.py get KEY
    jira.py search 'JQL'
    jira.py children [EPIC]
    jira.py create --summary S --body-file F [--type T] [--parent KEY] [--dry-run]
    jira.py edit KEY [--summary S] [--body-file F]
    jira.py comment KEY --body-file F
    jira.py attach KEY FILE [FILE ...]
    jira.py transition KEY 'In Progress'
    jira.py link KEY blocks OTHER_KEY
"""

from __future__ import annotations

import argparse
import base64
import collections.abc
import dataclasses
import json
import mimetypes
import pathlib
import secrets
import sys
import typing
import urllib.error
import urllib.request

CONFIG_PATH: typing.Final = pathlib.Path(".claude") / "jira.json"
FIELDS: typing.Final = "summary,issuetype,status,assignee,parent,priority,created,description"
LINK_TYPES: typing.Final = {"blocks": "Blocks", "relates": "Relates"}

Json = dict[str, typing.Any]


@dataclasses.dataclass(frozen=True, slots=True)
class JiraClient:
    """A Jira Cloud REST v2 client bound to one project config.

    Parameters
    ----------
    config : dict
        The parsed `.claude/jira.json`.
    auth : str
        The base64 `email:token` pair for HTTP basic auth.
    base_url : str
        The REST v2 root on the Atlassian gateway.
    """

    config: Json
    auth: str
    base_url: str

    def request(
        self,
        method: str,
        path: str,
        body: Json | None = None,
        *,
        raw: tuple[bytes, str] | None = None,
    ) -> typing.Any:
        """Send one request and return the decoded JSON body.

        Parameters
        ----------
        method : str
            The HTTP method.
        path : str
            The path below the REST v2 root, query string included.
        body : dict or None
            The JSON body to send, if any.
        raw : tuple of (bytes, str) or None
            A body that is not JSON, as its bytes and content type, for a file upload. Replaces
            `body`. It also sends `X-Atlassian-Token: no-check`, which Jira requires for
            attachments.

        Returns
        -------
        result : dict or list
            The decoded response, or an empty dict for an empty response.

        Raises
        ------
        SystemExit
            When Jira answers with an HTTP error; the message carries the status and the start of
            the body.
        """
        headers = {"Authorization": f"Basic {self.auth}", "Accept": "application/json"}
        if raw is not None:
            data, headers["Content-Type"] = raw
            headers["X-Atlassian-Token"] = "no-check"
        else:
            data = json.dumps(body).encode() if body is not None else None
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            self.base_url + path, method=method, data=data, headers=headers
        )

        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read()

        except urllib.error.HTTPError as e:
            sys.exit(f"{method} {path}: HTTP {e.code} {e.read().decode(errors='replace')[:500]}")

        result = json.loads(raw) if raw else {}

        return result


def find_config_file() -> pathlib.Path:
    """Find `.claude/jira.json` in the current directory or the nearest parent that has one.

    Returns
    -------
    result : pathlib.Path
        The config file.

    Raises
    ------
    SystemExit
        When no directory up to the filesystem root has the file.
    """
    cwd = pathlib.Path.cwd()
    candidates = [d / CONFIG_PATH for d in [cwd, *cwd.parents]]
    result = next((p for p in candidates if p.is_file()), None)
    if result is None:
        sys.exit(
            f"no {CONFIG_PATH} in this directory or its parents; see the jira skill for the format"
        )

    return result


def read_env_value(path: pathlib.Path, name: str) -> str:
    """Read one `NAME=value` entry from an env file, without exporting anything.

    Parameters
    ----------
    path : pathlib.Path
        The env file.
    name : str
        The variable to read.

    Returns
    -------
    result : str
        The value with surrounding whitespace and quotes removed.

    Raises
    ------
    SystemExit
        When the file has no such entry.
    """
    entries = (line.partition("=") for line in path.read_text().splitlines())
    result = next(
        (value.strip().strip("'\"") for key, _, value in entries if key.strip() == name), None
    )
    if result is None:
        sys.exit(f"{name} not found in {path}")

    return result


def open_client() -> JiraClient:
    """Build a client from the project config and its token.

    Returns
    -------
    result : JiraClient
        A client for the project's Jira site.
    """
    path = find_config_file()
    config = json.loads(path.read_text())
    root = path.parent.parent
    token = read_env_value(
        root / config.get("env_file", ".env"), config.get("token_env", "ATLASSIAN_TOKEN")
    )

    result = JiraClient(
        config=config,
        auth=base64.b64encode(f"{config['email']}:{token}".encode()).decode(),
        base_url=f"https://api.atlassian.com/ex/jira/{config['cloud_id']}/rest/api/2",
    )

    return result


def format_issue_line(issue: Json) -> str:
    """Format an issue as one line: key, type, status, assignee and summary."""
    fields = issue["fields"]
    assignee = (fields.get("assignee") or {}).get("displayName", "-")
    result = (
        f"{issue['key']}  {fields['issuetype']['name']}  [{fields['status']['name']}]  "
        f"{assignee}  {fields['summary']}"
    )

    return result


def _read_body(path: str | None) -> str | None:
    result = pathlib.Path(path).read_text() if path else None

    return result


def show_current_user(client: JiraClient, args: argparse.Namespace) -> None:
    """Print the name, email and account id the token logs in as."""
    me = client.request("GET", "/myself")
    print(me["displayName"], me["emailAddress"], me["accountId"])


def show_issue(client: JiraClient, args: argparse.Namespace) -> None:
    """Print one issue: its summary line, parent and description in wiki markup."""
    issue = client.request("GET", f"/issue/{args.key}?fields={FIELDS}")
    print(format_issue_line(issue))

    if parent := issue["fields"].get("parent"):
        print(f"parent: {parent['key']}")

    print()
    print(issue["fields"].get("description") or "(no description)")


def list_issues(client: JiraClient, args: argparse.Namespace) -> None:
    """Print one line per issue matching a JQL query, or per child of an epic for `children`."""
    if args.cmd == "search":
        jql = args.jql
    else:
        jql = f"parent = {args.epic or client.config['epic']} ORDER BY created DESC"

    found = client.request(
        "POST", "/search/jql", {"jql": jql, "fields": FIELDS.split(","), "maxResults": 100}
    )
    for issue in found["issues"]:
        print(format_issue_line(issue))


def create_issue(client: JiraClient, args: argparse.Namespace) -> None:
    """Create an issue under the configured epic and print its key.

    With `--dry-run` it prints the payload instead.
    """
    fields: Json = {
        "project": {"key": client.config["project"]},
        "issuetype": {"name": args.type or client.config.get("issue_type", "Task")},
        "summary": args.summary,
        "description": _read_body(args.body_file),
    }

    if parent := args.parent or client.config.get("epic"):
        fields["parent"] = {"key": parent}

    if client.config.get("assign_to_self", True):
        fields["assignee"] = {"accountId": client.request("GET", "/myself")["accountId"]}

    if args.dry_run:
        print(json.dumps({"fields": fields}, indent=2))
    else:
        print(client.request("POST", "/issue", {"fields": fields})["key"])


def edit_issue(client: JiraClient, args: argparse.Namespace) -> None:
    """Replace the summary, the description, or both."""
    changes = {"summary": args.summary, "description": _read_body(args.body_file)}
    fields = {k: v for k, v in changes.items() if v}
    if not fields:
        sys.exit("nothing to edit")

    client.request("PUT", f"/issue/{args.key}", {"fields": fields})
    print(f"{args.key} updated: {', '.join(fields)}")


def add_comment(client: JiraClient, args: argparse.Namespace) -> None:
    """Add a comment in wiki markup."""
    client.request("POST", f"/issue/{args.key}/comment", {"body": _read_body(args.body_file)})
    print(f"{args.key} commented")


def encode_multipart(paths: list[pathlib.Path]) -> tuple[bytes, str]:
    """Encode files as a `multipart/form-data` body, one `file` part each.

    It is the form Jira's attachment endpoint reads.

    Parameters
    ----------
    paths : list of pathlib.Path
        The files to send.

    Returns
    -------
    body : tuple of (bytes, str)
        The encoded body and its `Content-Type` header value, which carries the boundary.
    """
    boundary = secrets.token_hex(16)
    parts = []
    for path in paths:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        head = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        )
        parts.append(
            head.encode() + f"Content-Type: {mime}\r\n\r\n".encode() + path.read_bytes() + b"\r\n"
        )

    body = b"".join(parts) + f"--{boundary}--\r\n".encode()

    return body, f"multipart/form-data; boundary={boundary}"


def attach_files(client: JiraClient, args: argparse.Namespace) -> None:
    """Attach one or more files to an issue and print each as Jira stored it."""
    paths = [pathlib.Path(f) for f in args.files]
    if missing := [str(p) for p in paths if not p.is_file()]:
        sys.exit(f"not a file: {', '.join(missing)}")

    uploaded = client.request("POST", f"/issue/{args.key}/attachments", raw=encode_multipart(paths))
    for item in uploaded:
        print(f"{args.key} attached {item['filename']} ({item['size']} bytes)")


def transition_issue(client: JiraClient, args: argparse.Namespace) -> None:
    """Move an issue to a status, matched by transition or target status name."""
    options = client.request("GET", f"/issue/{args.key}/transitions")["transitions"]
    wanted = args.to.lower()
    match = next(
        (o for o in options if wanted in (o["name"].lower(), o["to"]["name"].lower())), None
    )
    if match is None:
        sys.exit(f"no transition to {args.to!r}; available: {[o['to']['name'] for o in options]}")

    client.request("POST", f"/issue/{args.key}/transitions", {"transition": {"id": match["id"]}})
    print(f"{args.key} -> {match['to']['name']}")


def link_issues(client: JiraClient, args: argparse.Namespace) -> None:
    """Link two issues and print the link as Jira states it."""
    # The API's inward/outward naming is easy to get backwards, so the link is read back rather
    # than assumed.
    body = {
        "type": {"name": LINK_TYPES[args.relation]},
        "inwardIssue": {"key": args.key},
        "outwardIssue": {"key": args.other},
    }
    client.request("POST", "/issueLink", body)

    links = client.request("GET", f"/issue/{args.key}?fields=issuelinks")["fields"]["issuelinks"]
    for link in links:
        if (outward := link.get("outwardIssue")) and outward["key"] == args.other:
            print(f"{args.key} {link['type']['outward']} {args.other}")

        if (inward := link.get("inwardIssue")) and inward["key"] == args.other:
            print(f"{args.key} {link['type']['inward']} {args.other}")


COMMANDS: typing.Final[
    dict[str, collections.abc.Callable[[JiraClient, argparse.Namespace], None]]
] = {
    "whoami": show_current_user,
    "get": show_issue,
    "search": list_issues,
    "children": list_issues,
    "create": create_issue,
    "edit": edit_issue,
    "comment": add_comment,
    "attach": attach_files,
    "transition": transition_issue,
    "link": link_issues,
}


def parse_args() -> argparse.Namespace:
    """Parse the command line into a command name and its arguments.

    Returns
    -------
    result : argparse.Namespace
        The parsed arguments; `cmd` names the command.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami")
    sub.add_parser("get").add_argument("key")
    sub.add_parser("search").add_argument("jql")
    sub.add_parser("children").add_argument("epic", nargs="?")

    create = sub.add_parser("create")
    create.add_argument("--summary", required=True)
    create.add_argument("--body-file", required=True)
    create.add_argument("--type")
    create.add_argument("--parent")
    create.add_argument("--dry-run", action="store_true")

    edit = sub.add_parser("edit")
    edit.add_argument("key")
    edit.add_argument("--summary")
    edit.add_argument("--body-file")

    comment = sub.add_parser("comment")
    comment.add_argument("key")
    comment.add_argument("--body-file", required=True)

    attach = sub.add_parser("attach")
    attach.add_argument("key")
    attach.add_argument("files", nargs="+")

    transition = sub.add_parser("transition")
    transition.add_argument("key")
    transition.add_argument("to")

    link = sub.add_parser("link")
    link.add_argument("key")
    link.add_argument("relation", choices=list(LINK_TYPES))
    link.add_argument("other")

    result = parser.parse_args()

    return result


def main() -> None:
    args = parse_args()
    COMMANDS[args.cmd](open_client(), args)


if __name__ == "__main__":
    main()
