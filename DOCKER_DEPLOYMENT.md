# Docker 镜像部署指南

本文档介绍如何在 Google Cloud Platform 上构建和部署 Docker 镜像。

## 项目配置

- **GCP 项目 ID**: `airy-web-476402-f4`
- **区域**: `northamerica-northeast2`
- **Artifact Registry 仓库**: `aether`
- **镜像基础路径**: `northamerica-northeast2-docker.pkg.dev/airy-web-476402-f4/aether`

## 先决条件

1. 已安装 Google Cloud SDK
2. 已配置 gcloud 认证: `gcloud auth login`
3. Docker Desktop 已安装并运行
4. Mac 环境下已配置跨平台构建 (Docker Buildx)

## 重要说明 (Mac Apple Silicon)

⚠️ **本项目在 Apple Silicon (ARM64) Mac 上开发，但需要构建 linux/amd64 架构的镜像以在 GCP 云端运行。**

所有构建命令已配置为使用 `--platform linux/amd64` 参数来确保兼容性。

## 本地构建和推送

### 方式 1: 使用脚本 (推荐)

```bash
# 使用 git commit SHA 作为标签
./scripts/build-and-push.sh

# 使用自定义标签
./scripts/build-and-push.sh v1.0.0
```

### 方式 2: 手动构建

```bash
# 设置环境变量
export CLOUDSDK_PYTHON=/usr/bin/python3
GCLOUD_BIN="$HOME/google-cloud-sdk/bin/gcloud"

# 构建镜像 (针对 amd64 架构)
docker buildx build --platform linux/amd64 \
  -t northamerica-northeast2-docker.pkg.dev/airy-web-476402-f4/aether/aether-app:latest \
  .

# 认证 Docker
"$GCLOUD_BIN" auth print-access-token | docker login -u oauth2accesstoken --password-stdin northamerica-northeast2-docker.pkg.dev

# 推送镜像
docker push northamerica-northeast2-docker.pkg.dev/airy-web-476402-f4/aether/aether-app:latest
```

## 使用 Google Cloud Build (推荐用于生产环境)

Cloud Build 在云端构建,避免本地架构问题,且速度更快。

### 手动触发构建

```bash
./scripts/cloud-build.sh
```

或使用 gcloud 命令:

```bash
export CLOUDSDK_PYTHON=/usr/bin/python3
~/google-cloud-sdk/bin/gcloud builds submit --config=cloudbuild.yaml .
```

### 设置自动化触发器 (推荐)

1. 前往 [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. 点击 "CREATE TRIGGER"
3. 配置:
   - **名称**: `aether-main-branch`
   - **Event**: Push to a branch
   - **Source**: 连接你的 Git 仓库
   - **Branch**: `^main$` (或 `^master$`)
   - **Configuration**: Cloud Build configuration file
   - **Location**: `/cloudbuild.yaml`
4. 保存后,每次推送到 main 分支将自动构建和推送镜像

## 查看和管理镜像

### 列出所有镜像

```bash
export CLOUDSDK_PYTHON=/usr/bin/python3
~/google-cloud-sdk/bin/gcloud artifacts docker images list \
  northamerica-northeast2-docker.pkg.dev/airy-web-476402-f4/aether
```

### 查看镜像详情

```bash
export CLOUDSDK_PYTHON=/usr/bin/python3
~/google-cloud-sdk/bin/gcloud artifacts docker images describe \
  northamerica-northeast2-docker.pkg.dev/airy-web-476402-f4/aether/aether-app:latest
```

### 删除镜像

```bash
export CLOUDSDK_PYTHON=/usr/bin/python3
~/google-cloud-sdk/bin/gcloud artifacts docker images delete \
  northamerica-northeast2-docker.pkg.dev/airy-web-476402-f4/aether/aether-app:TAG
```

## 在生产环境使用镜像

### 更新 docker-compose.yml (云端部署)

```yaml
services:
  web:
    image: northamerica-northeast2-docker.pkg.dev/airy-web-476402-f4/aether/aether-app:latest
    # ... 其他配置

  worker:
    image: northamerica-northeast2-docker.pkg.dev/airy-web-476402-f4/aether/aether-app:latest
    command: python -u -m app.worker
    # ... 其他配置
```

### Cloud Run 部署

```bash
export CLOUDSDK_PYTHON=/usr/bin/python3
~/google-cloud-sdk/bin/gcloud run deploy aether-web \
  --image northamerica-northeast2-docker.pkg.dev/airy-web-476402-f4/aether/aether-app:latest \
  --region northamerica-northeast2 \
  --platform managed
```

## 故障排查

### Docker 认证失败

如果遇到认证问题:

```bash
# 重新认证
export CLOUDSDK_PYTHON=/usr/bin/python3
~/google-cloud-sdk/bin/gcloud auth print-access-token | \
  docker login -u oauth2accesstoken --password-stdin \
  northamerica-northeast2-docker.pkg.dev
```

### 架构不匹配

确保始终使用 `--platform linux/amd64` 构建镜像:

```bash
docker buildx build --platform linux/amd64 ...
```

检查镜像架构:

```bash
docker inspect IMAGE_NAME --format='{{.Architecture}}'
# 应该输出: amd64
```

## 文件说明

- [Dockerfile](./Dockerfile) - Docker 镜像定义
- [cloudbuild.yaml](./cloudbuild.yaml) - Google Cloud Build 配置
- [docker-compose.yml](./docker-compose.yml) - 本地开发环境配置
- [scripts/build-and-push.sh](./scripts/build-and-push.sh) - 本地构建推送脚本
- [scripts/cloud-build.sh](./scripts/cloud-build.sh) - Cloud Build 触发脚本

## 最佳实践

1. **使用 Cloud Build**: 对于生产部署,使用 Cloud Build 而不是本地构建
2. **标签管理**: 使用语义化版本 (如 v1.0.0) 和 git SHA 标签
3. **自动化**: 设置 Cloud Build 触发器实现 CI/CD
4. **镜像清理**: 定期清理旧的未使用镜像
5. **安全扫描**: 启用 Artifact Registry 的漏洞扫描功能

## 相关链接

- [Google Artifact Registry 文档](https://cloud.google.com/artifact-registry/docs)
- [Cloud Build 文档](https://cloud.google.com/build/docs)
- [Docker Buildx 文档](https://docs.docker.com/buildx/working-with-buildx/)
