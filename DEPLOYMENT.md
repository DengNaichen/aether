# Aether 云端部署指南

## 架构概览

**本地环境:**
- Docker Compose (Web + PostgreSQL)
- 本地开发数据

**云端环境:**
- Google Cloud Run (Web API)
- Google Cloud SQL (PostgreSQL)
- Google Secret Manager (敏感信息)

## 前置要求

1. **安装 Google Cloud SDK**
   ```bash
   # macOS
   brew install --cask google-cloud-sdk

   # 或者访问: https://cloud.google.com/sdk/docs/install
   ```

2. **安装 Docker**
   ```bash
   brew install docker
   ```

3. **Google Cloud 账户**
   - 创建或选择一个 GCP 项目
   - 启用计费

## 部署步骤

### Step 1: 配置 Google Cloud

```bash
# 登录
gcloud auth login

# 设置项目 ID (替换为你的项目 ID)
export GOOGLE_CLOUD_PROJECT="your-project-id"
gcloud config set project $GOOGLE_CLOUD_PROJECT

# 配置 Docker 认证
gcloud auth configure-docker
```

### Step 2: 部署应用到 Cloud Run

这个脚本会自动:
- 构建 Docker 镜像
- 推送到 Google Container Registry
- 创建 Cloud SQL 实例
- 创建数据库和用户
- 部署到 Cloud Run

```bash
./scripts/deploy-to-cloud-run.sh
```

**提示:** 脚本会询问你设置数据库密码,请记住这个密码!

### Step 3: 迁移数据库数据

将本地 PostgreSQL 数据迁移到 Cloud SQL:

```bash
./scripts/migrate-database-to-cloud.sh
```

这个脚本会:
1. 从本地 Docker 容器导出数据
2. 上传到 Cloud Storage
3. 导入到 Cloud SQL
4. 验证导入结果
5. 清理临时文件

### Step 4: 验证部署

```bash
# 获取服务 URL
SERVICE_URL=$(gcloud run services describe aether-api --region=us-central1 --format='value(status.url)')

# 测试 API
curl $SERVICE_URL/health

# 测试数据库连接
curl $SERVICE_URL/api/v1/courses
```

## 配置说明

### 环境变量

Cloud Run 服务会自动配置以下环境变量:

- `ENVIRONMENT=production`
- `DATABASE_URL` - 自动连接到 Cloud SQL
- `SECRET_KEY` - 从 Secret Manager 读取
- `POSTGRES_PASSWORD` - 从 Secret Manager 读取

### 更新环境变量

如果需要添加其他环境变量(如 OpenAI API Key):

```bash
# 创建 secret
echo -n "your-api-key" | gcloud secrets create aether-openai-key \
    --data-file=- \
    --replication-policy=automatic

# 更新 Cloud Run 服务
gcloud run services update aether-api \
    --region=us-central1 \
    --update-secrets=OPENAI_API_KEY=aether-openai-key:latest
```

## 日常维护

### 查看日志

```bash
# 查看实时日志
gcloud run services logs tail aether-api --region=us-central1

# 查看最近的日志
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=aether-api" --limit 50
```

### 更新应用

```bash
# 1. 构建新镜像
docker build --platform linux/amd64 -t gcr.io/$GOOGLE_CLOUD_PROJECT/aether-api:latest .

# 2. 推送
docker push gcr.io/$GOOGLE_CLOUD_PROJECT/aether-api:latest

# 3. 更新 Cloud Run (会自动使用最新镜像)
gcloud run deploy aether-api \
    --image=gcr.io/$GOOGLE_CLOUD_PROJECT/aether-api:latest \
    --region=us-central1
```

或者直接重新运行:
```bash
./scripts/deploy-to-cloud-run.sh
```

### 数据库备份

Cloud SQL 会自动每天备份,但你也可以手动创建备份:

```bash
# 创建按需备份
gcloud sql backups create --instance=aether-db-instance

# 查看备份列表
gcloud sql backups list --instance=aether-db-instance

# 恢复备份
gcloud sql backups restore BACKUP_ID --backup-instance=aether-db-instance
```

### 本地数据库备份

```bash
./scripts/backup-local-database.sh
```

备份文件会保存在 `./backups/` 目录。

## 成本优化

### Cloud Run
- 按请求计费,没有流量时不收费
- 当前配置: 512Mi 内存, 1 CPU
- 建议: 低流量时使用 `--min-instances=0`

### Cloud SQL
- 当前配置: `db-f1-micro` (最便宜的实例)
- 10GB SSD 存储
- 自动备份

**预估成本:**
- Cloud Run: $0-5/月(低流量)
- Cloud SQL: ~$7-10/月
- 总计: ~$10-15/月

### 暂停服务(省钱)

```bash
# 停止 Cloud SQL 实例(不计算费用)
gcloud sql instances patch aether-db-instance --activation-policy=NEVER

# 恢复
gcloud sql instances patch aether-db-instance --activation-policy=ALWAYS
```

## 监控和告警

### 设置告警

```bash
# CPU 使用率告警
gcloud alpha monitoring policies create \
    --notification-channels=YOUR_CHANNEL_ID \
    --display-name="Aether High CPU" \
    --condition-display-name="CPU > 80%" \
    --condition-threshold-value=0.8 \
    --condition-threshold-duration=300s
```

### 性能监控

查看 Cloud Console:
- [Cloud Run Metrics](https://console.cloud.google.com/run)
- [Cloud SQL Monitoring](https://console.cloud.google.com/sql)

## 故障排查

### Cloud Run 无法启动

```bash
# 查看日志
gcloud run services logs read aether-api --region=us-central1 --limit=50

# 检查服务配置
gcloud run services describe aether-api --region=us-central1
```

### 数据库连接失败

1. 检查 Cloud SQL 实例状态:
   ```bash
   gcloud sql instances describe aether-db-instance
   ```

2. 验证 Cloud Run 有权限连接:
   ```bash
   gcloud run services describe aether-api --region=us-central1 --format="value(spec.template.spec.containers[0].env)"
   ```

3. 测试直接连接:
   ```bash
   gcloud sql connect aether-db-instance --user=aether_user --database=aether_db
   ```

### 回滚到之前的版本

```bash
# 查看所有版本
gcloud run revisions list --service=aether-api --region=us-central1

# 回滚到特定版本
gcloud run services update-traffic aether-api \
    --region=us-central1 \
    --to-revisions=REVISION_NAME=100
```

## 安全建议

1. **启用 Identity-Aware Proxy (IAP)**
   ```bash
   # 限制只有认证用户可以访问
   gcloud run services remove-iam-policy-binding aether-api \
       --region=us-central1 \
       --member="allUsers" \
       --role="roles/run.invoker"
   ```

2. **定期更新密钥**
   ```bash
   # 轮换 SECRET_KEY
   NEW_KEY=$(openssl rand -hex 32)
   echo -n "$NEW_KEY" | gcloud secrets versions add aether-secret-key --data-file=-
   ```

3. **限制 Cloud SQL 访问**
   - 已配置为只允许 Cloud Run 通过 Unix socket 连接
   - 不分配公共 IP

## 域名配置 (可选)

```bash
# 映射自定义域名
gcloud run services update aether-api \
    --region=us-central1 \
    --platform=managed \
    --add-cloudsql-instances=aether-db-instance

# 映射域名
gcloud beta run domain-mappings create \
    --service=aether-api \
    --domain=api.yourdomain.com \
    --region=us-central1
```

## 相关资源

- [Google Cloud Run 文档](https://cloud.google.com/run/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
