---
name: nacos-ops
description: 'Nacos 配置中心运维 — fetch/list/exists/push/diff/cross-diff/download, 多环境支持 (local/dev/uat/prod)'
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Nacos Ops Skill

封装 Nacos 标准 REST API (`/nacos/v1/cs/configs`),给 AI / 人类一句话操作配置。

## Step 0: 定位 skill 根

```bash
# frank install 装的会软链到三平台 skills/, 优先固定路径
SKILL_ROOT=$(ls -d ~/.claude/skills/nacos-ops 2>/dev/null \
          || ls -d ~/.codex/skills/nacos-ops 2>/dev/null \
          || ls -d ~/.opencode/skills/nacos-ops 2>/dev/null)
echo "SKILL_ROOT=$SKILL_ROOT"
```

## Step 1: Pre-flight 检查

```bash
test -f "$SKILL_ROOT/config.ini" || echo "需先 cp config.ini.example config.ini 填地址/账号"
test -d "$SKILL_ROOT/.venv" || echo "需先跑 bash setup.sh (或 setup.bat)"
```

| 缺失 | 修复 |
|------|------|
| `config.ini` | `cp config.ini.example config.ini` 然后填 `addr / username / password` |
| `.venv` | `bash setup.sh` (Mac/Linux) 或 `setup.bat` (Windows) |

## Step 2: 可用命令

| 命令 | 用途 | 破坏性 |
|------|------|--------|
| `nacos_config.py fetch --env <env>` | 拉取默认 dataId 配置 | ❌ 只读 |
| `nacos_config.py list --env <env>` | 列命名空间下全部配置 | ❌ 只读 |
| `nacos_config.py exists --env <env> --data-id <id>` | 检查存在 | ❌ 只读 |
| `nacos_config.py push --env <env> --file <path>` | 推配置上去 | ✅ 写 |
| `nacos_config.py cross-diff --env1 <a> --env2 <b>` | 两环境对比 | ❌ 只读 |
| `nacos_config.py download --env <env> --dir <out>` | 全部下载到本地 | ❌ 只读 (写本机) |
| `nacos_config.py diff --env <env>` | 跟本地 `project.path/config-examples/<env>/` 对比 | ❌ 只读 (需配 `project.path`) |

## Step 3: 调用示例

```bash
cd "$SKILL_ROOT"
.venv/bin/python nacos_config.py list --env local
.venv/bin/python nacos_config.py fetch --env local --data-id realtime-job.yaml
.venv/bin/python nacos_config.py cross-diff --env1 local --env2 uat
.venv/bin/python nacos_config.py push --env uat --file ./new-config.yaml
```

Windows 用户:
```cmd
.venv\Scripts\python.exe nacos_config.py list --env local
```

## 环境配置

`config.ini` 中 `[environments]` section 每行一个映射, key=本地别名, value=Nacos namespace:
```ini
[environments]
local = public        # docker-compose demo: namespace=public
dev   = dev-ns-id     # 真生产: 填 namespace UUID
uat   = uat-ns-id
prod  = prod-ns-id
```

## Demo 环境 (Docker)

`frank` 仓库 `deploy/test-stack/docker-compose.yml` 一键起本机 Nacos:
```bash
docker compose -f deploy/test-stack/docker-compose.yml up -d nacos
# Nacos 默认 http://localhost:8848/nacos, 账号 nacos/nacos
```
对应 `config.ini`:
```ini
[nacos]
addr = localhost:8848
username = nacos
password = nacos

[environments]
local = public
```

## API 参考

- 拉配置: `GET /nacos/v1/cs/configs?tenant=<ns>&dataId=<id>&group=<g>`
- 推配置: `POST /nacos/v1/cs/configs` form: `tenant/dataId/group/content/type=yaml`
- 列配置: `GET /nacos/v1/cs/configs?search=blur&tenant=<ns>`

认证: query param 携带 `username/password` (Nacos 1.x 标准方式)。

## 注意事项

- Nacos 2.x 要开 `nacos.core.auth.enabled=true` 才校验账号; 默认 docker 镜像可能不开
- `diff` 命令的 `project.path` 是**可选**配置 — 不配就 skip 这命令, 不影响其他
- `push` 后自动 verify (再 fetch 一次对比 hash), 失败会 warn
