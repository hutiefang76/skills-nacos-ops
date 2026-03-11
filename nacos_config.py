#!/usr/bin/env python3
"""Nacos configuration management: fetch, list, exists, push, diff, cross-diff, download."""

import argparse
import configparser
import difflib
import json
import os
import sys

import requests


def load_config():
    ini = configparser.ConfigParser()
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
    if not os.path.exists(cfg_path):
        print(f"[ERROR] config.ini not found at {cfg_path}", file=sys.stderr)
        print("  Copy config.ini.example → config.ini and fill in credentials.", file=sys.stderr)
        sys.exit(1)
    ini.read(cfg_path, encoding="utf-8")
    return ini


def resolve_namespace(ini, env):
    if not ini.has_option("environments", env):
        avail = ", ".join(ini.options("environments"))
        print(f"[ERROR] Unknown env '{env}'. Available: {avail}", file=sys.stderr)
        sys.exit(1)
    return ini.get("environments", env)


def _auth_params(ini):
    return {
        "username": ini.get("nacos", "username"),
        "password": ini.get("nacos", "password"),
    }


def _base_url(ini):
    return f"http://{ini.get('nacos', 'addr')}/nacos/v1/cs/configs"


def nacos_get(ini, namespace, data_id, group):
    resp = requests.get(_base_url(ini), params={
        "tenant": namespace, "dataId": data_id, "group": group,
        **_auth_params(ini),
    }, timeout=10)
    if resp.status_code != 200:
        return None
    return resp.text


def nacos_get_strict(ini, namespace, data_id, group):
    content = nacos_get(ini, namespace, data_id, group)
    if content is None:
        print(f"[ERROR] Nacos GET failed for {data_id} in {namespace}", file=sys.stderr)
        sys.exit(1)
    return content


def nacos_publish(ini, namespace, data_id, group, content):
    resp = requests.post(_base_url(ini), data={
        "tenant": namespace, "dataId": data_id, "group": group,
        "content": content, "type": "yaml",
        **_auth_params(ini),
    }, timeout=10)
    if resp.status_code != 200 or resp.text.strip().lower() != "true":
        print(f"[ERROR] Nacos POST failed: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)
    return True


def nacos_list(ini, namespace, group=None, page_size=200):
    """List all configs in a namespace via search API."""
    params = {
        "tenant": namespace,
        "search": "blur",
        "dataId": "",
        "group": group or "",
        "pageNo": 1,
        "pageSize": page_size,
        **_auth_params(ini),
    }
    resp = requests.get(_base_url(ini), params=params, timeout=10)
    if resp.status_code != 200:
        print(f"[ERROR] Nacos list failed: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)
    try:
        return resp.json()
    except Exception:
        # Nacos v1 search returns JSON with pageItems
        print(f"[ERROR] Unexpected response format", file=sys.stderr)
        sys.exit(1)


def _defaults(args, ini):
    data_id = getattr(args, "data_id", None) or ini.get("defaults", "data_id")
    group = getattr(args, "group", None) or ini.get("defaults", "group")
    return data_id, group


# ============================================================
# Subcommands
# ============================================================

def cmd_fetch(args, ini):
    namespace = resolve_namespace(ini, args.env)
    data_id, group = _defaults(args, ini)
    print(nacos_get_strict(ini, namespace, data_id, group))


def cmd_list(args, ini):
    namespace = resolve_namespace(ini, args.env)
    _, group = _defaults(args, ini)
    result = nacos_list(ini, namespace, group if not args.all_groups else None)

    if isinstance(result, dict) and "pageItems" in result:
        items = result["pageItems"]
        print(f"Configs in namespace '{args.env}' ({len(items)} items):\n")
        for item in items:
            did = item.get("dataId", "?")
            grp = item.get("group", "?")
            content = item.get("content", "")
            size = len(content) if content else 0
            print(f"  [{grp}] {did}  ({size} bytes)")
    else:
        print(f"[WARN] Unexpected response, raw:\n{result}")


def cmd_exists(args, ini):
    namespace = resolve_namespace(ini, args.env)
    data_id, group = _defaults(args, ini)
    if args.data_id:
        data_id = args.data_id
    content = nacos_get(ini, namespace, data_id, group)
    if content is not None:
        print(f"[YES] '{data_id}' exists in {args.env} (group={group}, {len(content)} bytes)")
    else:
        print(f"[NO] '{data_id}' not found in {args.env} (group={group})")


def cmd_push(args, ini):
    namespace = resolve_namespace(ini, args.env)
    data_id, group = _defaults(args, ini)

    if not os.path.exists(args.file):
        print(f"[ERROR] File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"Pushing to env={args.env} namespace={namespace} dataId={data_id} group={group}")
    print(f"  File: {args.file} ({len(content)} bytes)")

    nacos_publish(ini, namespace, data_id, group, content)
    print("[OK] Published")

    verify = nacos_get_strict(ini, namespace, data_id, group)
    if verify.strip() == content.strip():
        print("[OK] Verified — remote matches local")
    else:
        print("[WARN] Remote content differs from pushed content", file=sys.stderr)


def cmd_diff(args, ini):
    namespace = resolve_namespace(ini, args.env)
    data_id, group = _defaults(args, ini)

    project_path = ini.get("project", "path")
    local_file = os.path.join(project_path, "config-examples", args.env, "nacos.yaml")
    if not os.path.exists(local_file):
        print(f"[ERROR] Local config not found: {local_file}", file=sys.stderr)
        sys.exit(1)

    with open(local_file, "r", encoding="utf-8") as f:
        local_lines = f.readlines()

    remote_content = nacos_get_strict(ini, namespace, data_id, group)
    remote_lines = remote_content.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        local_lines, remote_lines,
        fromfile=f"local ({local_file})",
        tofile=f"nacos ({args.env}/{data_id})",
    ))

    if not diff:
        print("[OK] No differences — local and remote are identical")
    else:
        for line in diff:
            print(line, end="" if line.endswith("\n") else "\n")


def cmd_cross_diff(args, ini):
    ns1 = resolve_namespace(ini, args.env1)
    ns2 = resolve_namespace(ini, args.env2)
    data_id, group = _defaults(args, ini)

    content1 = nacos_get_strict(ini, ns1, data_id, group)
    content2 = nacos_get_strict(ini, ns2, data_id, group)

    lines1 = content1.splitlines(keepends=True)
    lines2 = content2.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        lines1, lines2,
        fromfile=f"nacos ({args.env1}/{data_id})",
        tofile=f"nacos ({args.env2}/{data_id})",
    ))

    if not diff:
        print(f"[OK] No differences between {args.env1} and {args.env2}")
    else:
        for line in diff:
            print(line, end="" if line.endswith("\n") else "\n")


def cmd_download(args, ini):
    namespace = resolve_namespace(ini, args.env)
    data_id, group = _defaults(args, ini)

    content = nacos_get_strict(ini, namespace, data_id, group)

    if args.output:
        out_path = args.output
    else:
        project_path = ini.get("project", "path")
        out_dir = os.path.join(project_path, "config-examples", args.env)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, data_id)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] Downloaded {data_id} from {args.env} → {out_path} ({len(content)} bytes)")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Nacos config management for Flink CDC jobs")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p, env_required=True):
        p.add_argument("--env", required=env_required, help="Environment name (local/uat/prod)")
        p.add_argument("--data-id", help="Nacos data ID")
        p.add_argument("--group", help="Nacos group")

    # fetch
    p_fetch = sub.add_parser("fetch", help="Fetch config content from Nacos")
    add_common(p_fetch)

    # list
    p_list = sub.add_parser("list", help="List all configs in a namespace")
    p_list.add_argument("--env", required=True, help="Environment name")
    p_list.add_argument("--all-groups", action="store_true", help="List across all groups")
    p_list.add_argument("--data-id", help=argparse.SUPPRESS)
    p_list.add_argument("--group", help="Filter by group")

    # exists
    p_exists = sub.add_parser("exists", help="Check if a specific config exists")
    add_common(p_exists)

    # push
    p_push = sub.add_parser("push", help="Push local file to Nacos")
    add_common(p_push)
    p_push.add_argument("--file", required=True, help="Path to YAML file")

    # diff (local vs remote)
    p_diff = sub.add_parser("diff", help="Diff local project config vs Nacos remote")
    add_common(p_diff)

    # cross-diff (env1 vs env2)
    p_xdiff = sub.add_parser("cross-diff", help="Diff config between two environments")
    p_xdiff.add_argument("--env1", required=True, help="First environment")
    p_xdiff.add_argument("--env2", required=True, help="Second environment")
    p_xdiff.add_argument("--data-id", help="Nacos data ID")
    p_xdiff.add_argument("--group", help="Nacos group")

    # download
    p_dl = sub.add_parser("download", help="Download Nacos config to local file")
    add_common(p_dl)
    p_dl.add_argument("--output", help="Output file path (default: config-examples/<env>/<data_id>)")

    args = parser.parse_args()
    ini = load_config()

    cmds = {
        "fetch": cmd_fetch, "list": cmd_list, "exists": cmd_exists,
        "push": cmd_push, "diff": cmd_diff, "cross-diff": cmd_cross_diff,
        "download": cmd_download,
    }
    cmds[args.command](args, ini)


if __name__ == "__main__":
    main()
