# 卡密登录计划（延期，非 v1）

> 状态：**延期**。当前 `clean_client` 走免登录。  
> 本文档保留原版逆向结论与未来接入计划，避免后续返工时丢上下文。

## 原版 Nirvana 结论

卡密**不是客户端本地生成**，而是远程后台管理系统发卡。

| 项 | 值 |
| --- | --- |
| 登录 API 根 | `http://36.138.222.171:124/prod-api` |
| 第三方/登录入口 | `http://36.138.222.171:124/prod-api/third` |
| 公告示例 | `.../prod-api/store/notice/{id}` |
| 软件更新 | `http://36.138.222.171:3000/api/version` |

客户端侧已确认能力：

- `FluentLoginDialog`
  - `_check_key`（卡密模式）
  - `_check_account_password`（账号密码模式）
  - `_do_login` / `_on_login_result`
- 登录后：
  - `_ensure_login`
  - `_start_heartbeat` / `_run_heartbeat` / `_stop_heartbeat`
  - `_fetch_and_show_key_info` / `_update_key_info_widget`
  - `_show_key_info_dialog`（含 `_update_remaining_label` 倒计时）
  - `_logout_login_key`

因此原版至少具备：**发卡后台 + 卡密/账密登录 + 心跳校验 + 剩余时长展示**。  
本仓库**没有**拿到该后台的源码；发卡 UI/数据库应在 `36.138.222.171:124` 那套 `prod-api` 服务端。

## clean_client 未来方案（建议）

推荐自建，而不是绑死原服务器：

```text
admin_api/          # 生成卡密、设置时长、禁用卡、查日志
clean_client/auth/  # 登录框、本地缓存 token、心跳线程
```

最小接口草案：

1. `POST /auth/login` `{ "card_key": "..." }` → `{ token, expire_at }`
2. `POST /auth/heartbeat` `{ "token": "..." }` → `{ ok, expire_at }`
3. `POST /admin/cards`（后台）生成卡：时长/次数/备注

客户端策略：

- 启动先登录；失败则不进主循环
- 心跳失败 / 过期 → 停止引擎并提示
- 本地可记住卡密（可选加密存储）

## 为什么 v1 先不做

- 当前优先打通：像素协议识别 → dry-run → 真按键
- 免登录便于本地开发和测试
- 卡密需要额外的服务端与运维，不应阻塞战斗管线

## 恢复工作时检查清单

- [ ] 选定自建后台还是对接原 `prod-api`
- [ ] 定卡密格式与有效期模型
- [ ] 给 `clean_client` 加登录门闩（未登录禁止 `EngineLoop.start`）
- [ ] 心跳与剩余时间 UI
- [ ] 更新设计文档 success criteria
