# RAG应用Docker使用指南

## 快速开始

### 1. 准备配置文件

```bash
# 复制配置示例并编辑
cp config.yaml.example config.yaml

# 编辑 config.yaml，确保 Qdrant 配置指向 docker-compose 服务名
# host: qdrant (而不是 localhost)
```

### 2. 放置文档

将需要索引的文档放入 `data/` 目录（支持多种格式：txt、pdf、docx等）

### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose up --build

# 或者后台运行
docker-compose up -d --build
```

## 常用命令

```bash
# 只启动Qdrant服务
docker-compose up qdrant -d

# 查看日志
docker-compose logs -f app
docker-compose logs -f qdrant

# 停止服务
docker-compose down

# 停止并删除数据卷（谨慎使用）
docker-compose down -v

# 重建镜像
docker-compose build --no-cache
```

## 配置文件示例 (config.yaml)

```yaml
llm:
  api_key: "your-api-key"
  api_base: "https://api.deepseek.com/v1"
  model: "deepseek-chat"

embedding:
  model_name: "BAAI/bge-small-zh-v1.5"

vector_store:
  host: "qdrant"  # 使用服务名，不是localhost
  port: 6333
  collection_name: "documents"

query:
  similarity_top_k: 5
```

## 数据持久化

- **Qdrant数据**: 使用Docker volume `qdrant_storage` 持久化
- **应用数据**: `data/` 目录通过bind mount挂载到容器中

## 注意事项

1. 首次运行会下载Embedding模型，可能需要较长时间
2. 确保config.yaml中的API密钥正确配置
3. Qdrant服务会先启动，应用会等待Qdrant健康检查通过后才运行
