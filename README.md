# skills-nacos-ops

Nacos 配置中心运维 skill — frank/Claude/Codex/Opencode 都能装。

## 装

```bash
# 通过 frank (推荐)
frank install nacos-ops

# 或直接 git clone 后手动接入 ~/.claude/skills/
git clone https://github.com/hutiefang76/skills-nacos-ops.git ~/.claude/skills/nacos-ops
```

## 用

```bash
cd ~/.claude/skills/nacos-ops
bash setup.sh                    # Mac/Linux
# setup.bat                      # Windows

cp config.ini.example config.ini # 改成你环境的 nacos 地址/账号
.venv/bin/python nacos_config.py list --env local
```

完整命令清单见 `SKILL.md`。

## Demo

```bash
# 本机起一个 Nacos (用 frank 仓库的 demo stack):
git clone https://github.com/hutiefang76/skills-frank.git
cd skills-frank/deploy/test-stack
docker compose up -d nacos
# 浏览器开 http://localhost:8848/nacos , 账号 nacos/nacos
```

然后 `config.ini` 用 `localhost:8848 / nacos / nacos`, 直接 `list --env local` 就有结果。

## 平台支持

| OS | setup | 备注 |
|----|-------|------|
| macOS | `bash setup.sh` | 需要 python 3.8+ |
| Linux | `bash setup.sh` | 同上 |
| Windows | `setup.bat` | python 3.8+, venv 在 `.venv\Scripts\` |

## License

MIT
