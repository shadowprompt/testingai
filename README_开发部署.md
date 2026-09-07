# 开发部署说明

## 1. 推荐：Docker Compose

```bash
unzip AI政策文本测评系统_完整部署包.zip
cd AI政策文本测评系统_完整部署包
cp .env.example .env
```

生成随机密钥：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

把结果写入 `.env` 的 `SECRET_KEY`。

启动：

```bash
docker compose up -d --build
```

测试地址：

```text
http://服务器IP:8088
```

## 2. 正式服务器建议

- 使用正式域名和 HTTPS
- `COOKIE_SECURE=1`
- 只通过 Nginx 暴露 80/443，不直接暴露 8000
- 如需限制访问人员，请在学校统一认证、VPN、Nginx Basic Auth 或网关层完成，不要在本系统里重新维护账号密码
- SQLite适合当前小规模使用；多人高并发后建议切换 PostgreSQL
- 数据目录定时备份
- 配置日志轮转、依赖漏洞扫描和服务器最小权限

## 3. 数据访问设计

系统不设用户账户。每次测评创建一个随机 `access_token`，结果页URL形如：

```text
/a/高强度随机令牌
```

首页只显示“当前浏览器最近创建的测评”，不会公开列出其他人的结果。

## 4. 文件上传

支持：`.txt .md .docx .pdf .html .htm`

上传文件仅提取文本内容，不保存原始文件。单文件建议不超过 3MB；Nginx总请求限制为20MB。

## 5. 人工复核

知道结果随机链接的人可以提交复核。机器初评分、人工修正分和复核记录分开保存。

## 6. 代码结构

```text
app.py              Flask路由、上传、导出
scoring.py          八维评价与原文审校规则
db.py               SQLite存储
templates/          页面模板
static/             CSS/JS
Dockerfile
docker-compose.yml
nginx.conf
METHOD.md
SECURITY.md
```

## 结果页面新增路由

- `/a/<token>`：综合测评结果、待测政策文本审校、人工复核
- `/a/<token>/export`：独立导出页面
- `/a/<token>/word`：Word完整报告
- `/a/<token>/csv`：评分CSV
- `/a/<token>/proofreading.csv`：政策文本审校清单CSV
