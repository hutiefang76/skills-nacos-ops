---
name: nacos-config
description: "Fetch, list, push, diff, cross-diff and download Nacos configuration for Flink CDC jobs. Use when asked about Nacos配置, 拉取配置, 推送配置, 配置对比, 环境差异, 下载配置, realtime-job.yaml, MAGNOLIA_GROUP, or config sync. Keywords: nacos, 配置管理, fetch, list, push, diff, cross-diff, download, realtime-job."
allowed-tools: Bash, Read
---

# Nacos Config — Flink CDC 作业配置管理

**Skill root**: Locate the directory containing `nacos_config.py`.
Search order (stop at first match):
1. `~/workspace/skills/nacos-config`
2. `D:\workspace\skills\nacos-config` (Windows default)
3. Fallback: `find ~ -name "nacos_config.py" -maxdepth 6 2>/dev/null | head -1 | xargs dirname`

All commands below `cd` into skill root first.

## Pre-flight Check

```bash
ls <skill_root>/nacos_config.py
ls <skill_root>/config.ini
python -c "import requests" 2>&1
```

| Failure | Tell user |
|---------|-----------|
| `nacos_config.py` not found | "请确认 skill 目录存在" |
| `config.ini` missing | "请复制 `config.ini.example` → `config.ini`，填入 Nacos 凭证" |
| `requests` not found | "请运行 `<skill_root>/setup.bat` 安装依赖" |

## Decision Tree

```
User request
├─ 查看/拉取配置       → fetch --env <env>
├─ 列出全部配置        → list --env <env> [--all-groups]
├─ 检查配置是否存在     → exists --env <env> [--data-id <id>]
├─ 推送配置            → push --env <env> --file <path>
├─ 本地 vs 远端对比     → diff --env <env>
├─ 环境间对比          → cross-diff --env1 <e1> --env2 <e2>
└─ 下载配置到本地       → download --env <env> [--output <path>]
```

## Commands

```bash
cd <skill_root>

# 拉取配置到 stdout
python nacos_config.py fetch --env local

# 列出 namespace 下全部配置
python nacos_config.py list --env local
python nacos_config.py list --env uat --all-groups

# 检查指定配置是否存在
python nacos_config.py exists --env local
python nacos_config.py exists --env uat --data-id my-service.yaml

# 推送本地文件到 Nacos
python nacos_config.py push --env local --file config-examples/local/nacos.yaml

# 本地项目配置 vs Nacos 远端
python nacos_config.py diff --env local

# 环境间对比（如 local vs uat）
python nacos_config.py cross-diff --env1 local --env2 uat

# 下载配置到本地文件
python nacos_config.py download --env uat
python nacos_config.py download --env prod --output /tmp/prod-config.yaml
```

## Parameters

| Param | Required | Notes |
|-------|----------|-------|
| command | yes | `fetch` `list` `exists` `push` `diff` `cross-diff` `download` |
| `--env` | yes (except cross-diff) | config.ini 中 `[environments]` 定义的环境名 |
| `--env1` / `--env2` | cross-diff only | 两个对比环境 |
| `--file` | push only | YAML 文件路径 |
| `--data-id` | no | Nacos data ID（默认 `realtime-job.yaml`） |
| `--group` | no | Nacos group（默认 `MAGNOLIA_GROUP`） |
| `--all-groups` | list only | 列出全部 group 的配置 |
| `--output` | download only | 输出路径（默认 `config-examples/<env>/<data_id>`） |

## Config Structure

```ini
[nacos]
addr = HOST:PORT
username = nacos
password = PASSWORD

[environments]
local = local
uat = uat
prod = prod

[defaults]
data_id = realtime-job.yaml
group = MAGNOLIA_GROUP

[project]
path = /path/to/realtime-job
```
