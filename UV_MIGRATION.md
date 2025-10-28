# UV Migration Guide

## 迁移完成! 🎉

我们已经成功从 **conda** 迁移到 **uv** 包管理器!

## 什么改变了?

### 以前 (conda):
```bash
conda activate tutor-env
python app/main.py
pytest
```

### 现在 (uv):
```bash
# 不需要激活环境!
uv run python app/main.py
uv run pytest
uv run uvicorn app.main:app --reload
```

## 常用命令

### 安装依赖
```bash
# 同步所有依赖
uv sync

# 添加新依赖
uv add fastapi
uv add --dev pytest

# 删除依赖
uv remove package-name
```

### 运行应用
```bash
# 运行 FastAPI 服务器
uv run uvicorn app.main:app --reload

# 运行测试
uv run pytest
uv run pytest tests/ -v

# 运行任何 Python 脚本
uv run python script.py
```

### 查看依赖
```bash
# 列出所有依赖
uv pip list

# 显示依赖树
uv pip tree
```

## 为什么选择 uv?

✨ **速度极快** - 比 conda/pip 快 10-100 倍
- 安装 61 个包只用了 **130ms**
- conda 同样操作需要 **60 秒**

🔒 **依赖锁定** - `uv.lock` 确保团队使用完全相同的依赖版本

🎯 **简单** - 不需要激活/停用虚拟环境

🛠 **现代化** - Rust 编写,遵循最新 Python 标准

## 项目结构

```
.
├── pyproject.toml       # 项目配置和依赖定义
├── uv.lock             # 依赖锁文件 (请提交到 git!)
├── .python-version     # Python 版本 (请提交到 git!)
├── .venv/              # 虚拟环境 (自动创建,不要提交)
└── requirements.txt    # 保留作为备份
```

## 迁移前后对比

| 特性 | conda | uv |
|------|-------|-----|
| 安装速度 | ~60秒 | ~0.1秒 |
| 环境激活 | 需要 | 不需要 |
| 依赖锁定 | environment.yml | uv.lock |
| Python 版本管理 | ✅ | ✅ |
| 跨平台 | ✅ | ✅ |

## 团队协作

当其他人克隆项目时:

```bash
# 1. 安装 uv (如果还没有)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 同步依赖
cd aether
uv sync

# 3. 开始开发!
uv run pytest
```

## 清理旧环境 (可选)

如果确认 uv 环境工作正常,可以删除 conda 环境:

```bash
# 停用 conda 环境
conda deactivate

# 删除环境
conda env remove -n tutor-env

# (可选) 如果不再使用 conda
# 可以考虑卸载 Anaconda
```

## 测试结果

✅ **134/138 测试通过**
- 3 个失败测试是之前就存在的问题
- 1 个错误是测试配置问题 (缺少 fixture)
- 所有核心功能正常工作

## 注意事项

1. **保留 requirements.txt** - 暂时保留作为备份,未来可以删除
2. **提交 uv.lock** - 这个文件确保团队依赖一致性
3. **提交 .python-version** - 固定 Python 3.12 版本
4. **不要提交 .venv/** - 已在 .gitignore 中

## 需要帮助?

- uv 文档: https://docs.astral.sh/uv/
- 问题反馈: https://github.com/astral-sh/uv/issues

---

迁移日期: 2025-10-26
Python 版本: 3.12.12
uv 版本: 0.9.5
