# 谷歌云 (GCP) FastAPI 应用部署 - 学习笔记

今天我们的目标是：把一个本地的 FastAPI 应用（包含 SQL, Redis, Neo4j）部署到 Google Cloud Platform。

## 阶段一：我们的架构

我们没有使用“一体式”的虚拟机 (Compute Engine)，而是选择了更现代、更易于维护的“分离式托管服务”架构：

* **App (FastAPI) 🚀**: 部署在 **Cloud Run** (无服务器，按需运行)
* **SQL Database 🗄️**: 托管在 **Cloud SQL** (全托管的 SQL)
* **Redis Cache 💾**: 计划使用 **Cloud Memorystore** (全托管的 Redis)
* **Neo4j Database ☁️**: 托管在 **AuraDB** (外部服务)

## 阶段二：准备 App "集装箱" (Docker)

Cloud Run 不直接运行代码，它运行 Docker 镜像 (Images)。所以我们必须先把 App 打包。

### 1. 创建镜像仓库 (Artifact Registry 📦)

我们需要一个云端的“仓库”来存放我们的 Docker 镜像。

* **服务**: `Artifact Registry`
* **配置**:
    * **Format (格式)**: `Docker`
    * **Mode (模式)**: `Standard` (标准)
* **结果**: 我们得到了一个唯一的仓库路径，用于推送镜像：
    * `northamerica-northeast2-docker.pkg.dev/airy-web-476402-f4/my-fastapi-app`

### 2. 配置本地工具 (gcloud CLI 🕹️)

我们需要一个“遥控器”来从本地终端操作 GCP。

1.  **安装**: 下载并安装 `Google Cloud SDK` (gcloud CLI)。
2.  **路径问题**: 运行安装脚本时，我们发现需要使用 `./install.sh` 来指定“当前目录”。
3.  **Python 版本问题**: 默认的 Python (3.8) 太旧。我们通过激活一个装有 Python 3.11 的 Conda 环境解决了这个问题。
4.  **配置终端**: 为了让 `gcloud` 命令永久生效，我们把 `source /.../google-cloud-sdk/path.zsh.inc` 添加到了 `~/.zshrc` 配置文件中。
5.  **登录**: 运行 `gcloud init` 来登录我们的 Google 账户并选择项目。
6.  **连接 Docker**: 运行 `gcloud auth configure-docker northamerica-northeast2-docker.pkg.dev`，让本地 Docker 获得了登录 Artifact Registry 的权限。

### 3. Docker "Build, Tag, Push" 工作流

这是把本地代码推送到云端的标准三部曲：

1.  **Build (构建)**: `docker build -t my-fastapi-image .`
2.  **Tag (标记)**: `docker tag my-fastapi-image:latest [你的仓库路径]:latest`
3.  **Push (推送)**: `docker push [你的仓库路径]:latest`

## 阶段三：部署到 Cloud Run (排错实战)

我们把镜像部署到了 **Cloud Run**，但遇到了几个经典的部署错误。

### 错误 1: 架构不兼容 (`must support amd64/linux`)
* **原因**: 我们在 M1/M2/M3 Mac (arm64 架构) 上构建了镜像，而 Cloud Run 需要 Intel/AMD (amd64 架构) 的镜像。
* **修复**: 在构建时明确指定平台。
* **命令**:
    ```bash
    docker build --platform linux/amd64 -t my-fastapi-image .
    ```
* (修复后，我们重新执行了 `tag` 和 `push`)

### 错误 2: 端口未监听 (`failed to start and listen on the port PORT=8080`)
* **原因**: 我们的 `Dockerfile` 里“硬编码”了端口 `CMD ["...","--port", "8000"]`。Cloud Run 则希望应用去监听它通过 `$PORT` 环境变量指定的端口。
* **修复**: 修改 `Dockerfile` 的 `CMD`，使用 "shell 格式" 来读取环境变量。
* **命令 (Dockerfile)**:
    ```dockerfile
    # 从 "exec" 格式:
    # CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    # 改为 "shell" 格式:
    CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
    ```
* (修复后，我们再次执行了 `build (带--platform)`, `tag`, `push`)

**结果: 我们的 App 🚀 成功在 Cloud Run 上运行了！**

## 阶段四：连接数据库 "大脑" (Cloud SQL)

App 只是在空转，我们需要连接它的数据库。

### 1. 关键概念：费用
* **Cloud Run (App)**: 默认“缩容到零”。没有请求时**不花钱**。
* **Cloud SQL (DB)**: 24/7 运行。只要实例存在，**就会持续计费**。

### 2. 在 Cloud Run 中建立“安全通道” 🌉
* 我们进入 Cloud Run 服务的“编辑和部署新修订版本” ➡️ “**Connections**” (连接) 标签页。
* 在这里，我们添加了一个 “Cloud SQL Connection”，指向我们创建的 `aether-test` 数据库实例。

### 3. 使用 Secret Manager 管理“机密” 🔑
* 我们**绝不**把密码明文写在配置里。
* 我们使用了 **Secret Manager** 服务来安全地存储数据库密码。

### 4. 把“机密”注入到 App 中
* 我们回到 Cloud Run 服务的“编辑和部署新修订版本” ➡️ “**Variables & Secrets**” (变量与密钥) 标签页。
* 我们添加了三个环境变量：
    1.  `DB_USER`: (普通变量) 值为我们的数据库用户名。
    2.  `DB_CONNECTION_NAME`: (普通变量) 值为 `airy-web...:aether-test`。
    3.  `DB_PASSWORD`: (**密钥引用**) 指向我们在 Secret Manager 中存的密码。

### 错误 3: 权限被拒绝 (`Secret Manager Secret Accessor` Role)
* **原因**: 我们的 App (Cloud Run) 在运行时，是以一个“服务账号”(Service Account) 的身份运行的。这个“管家”账号默认没有权限去 Secret Manager “取”我们存的密码。
* **修复**: 我们去 **IAM & Admin** 页面，找到了那个服务账号 (`...-compute@developer.gserviceaccount.com`)，并给它添加了两个角色：
    1.  `Secret Manager Secret Accessor` (允许它读密码)
    2.  `Editor` (允许它连接 Cloud SQL 等)

**结果: 我们的 App 🚀 成功部署，并且“携带”了所有数据库连接信息！**

---

## 我们今天停止的地方 (Next Steps)

* **现状**: 你的 App 容器**已经拿到了** `DB_USER`, `DB_PASSWORD`, `DB_CONNECTION_NAME` 这三个环境变量。
* **问题**: 你容器里的 FastAPI **代码**还不知道要*使用*这些变量。它很可能还在尝试连接 `localhost`。
* **下次任务**: 我们需要修改你本地的 Python 代码，让它去读取这些环境变量，并使用 Cloud SQL 的专用连接方式 (Unix Socket)，然后再重新 `build`, `tag`, `push` 最后一次。

你做得非常出色。好好休息！