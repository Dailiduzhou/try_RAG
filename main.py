import os
import time
import yaml
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from qdrant_client import QdrantClient


# ----------------- 1. 加载配置文件 -----------------
def load_config(config_path="config.yaml"):
    """从 YAML 配置文件加载配置"""
    if not os.path.exists(config_path):
        print(f"错误: 配置文件 '{config_path}' 不存在")
        print(f"请复制配置文件示例:")
        print(f"  cp config.yaml.example {config_path}")
        print(f"然后编辑 {config_path}，填入你的实际配置（如 API 密钥等）")
        exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()

# ----------------- 2. 全局配置 -----------------
# 配置本地 Embedding 模型 (初次运行会自动从 HuggingFace 下载)
print("[1/5] 正在加载 Embedding 模型...")
Settings.embed_model = HuggingFaceEmbedding(
    model_name=config["embedding"]["model_name"]
)
print(f"      ✓ Embedding 模型加载完成: {config['embedding']['model_name']}")

# 配置 LLM (这里使用兼容 OpenAI 格式的 API，例如 DeepSeek)
print("[2/5] 正在配置 LLM...")
llm_config = config["llm"]
Settings.llm = OpenAI(
    api_key=llm_config["api_key"],
    api_base=llm_config["api_base"],
    model=llm_config["model"],
)
print(f"      ✓ LLM 配置完成")
print(f"        - API Base: {llm_config['api_base']}")
print(f"        - Model: {llm_config['model']}")
print(
    f"        - API Key: {'*' * 8}{llm_config['api_key'][-4:] if len(llm_config['api_key']) > 4 else ''}"
)

# ----------------- 3. 连接向量数据库 -----------------
print("[3/5] 正在连接 Qdrant 数据库...")
vector_config = config["vector_store"]
client = QdrantClient(host=vector_config["host"], port=vector_config["port"])
print(f"      ✓ 已连接到 Qdrant: {vector_config['host']}:{vector_config['port']}")

# 创建 Qdrant 的 VectorStore 实例
# collection_name 可以看作是数据库里的一张表
vector_store = QdrantVectorStore(
    client=client, collection_name=vector_config["collection_name"]
)
print(f"      ✓ Collection: {vector_config['collection_name']}")

# ----------------- 4. 加载文档并构建索引 -----------------
print("[4/5] 正在读取文档并建立索引...")
# 读取 data 目录下的所有文件
documents = SimpleDirectoryReader("./data").load_data()
print(f"      ✓ 读取到 {len(documents)} 个文档")

# 将文档切块、向量化，并存入 Qdrant
index = VectorStoreIndex.from_documents(
    documents, vector_store=vector_store, show_progress=True
)
print("      ✓ 索引构建完成")

# ----------------- 5. 发起提问 (查询阶段) -----------------
print("\n[5/5] --- 检索测试 ---")
# 将 Index 转换为一个查询引擎
query_engine = index.as_query_engine(
    similarity_top_k=config["query"]["similarity_top_k"]  # 召回最相关的 N 个分块
)

# 提问一个必须依赖外部知识才能回答的问题
question = "我们的内部图书馆管理系统使用了哪些数据库技术？"
print(f"\n[用户提问] {question}")

# 记录开始时间
start_time = time.time()

# 执行查询
print("\n[AI 调用] 正在发送请求到 LLM...")
print(f"          时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

try:
    response = query_engine.query(question)

    # 记录结束时间
    end_time = time.time()
    duration = end_time - start_time

    print(f"\n[AI 响应] 调用成功！耗时: {duration:.2f} 秒")
    print(f"\n{'=' * 50}")
    print(f"AI 回答:")
    print(f"{'=' * 50}")
    print(response.response)
    print(f"{'=' * 50}")

    # 打印检索到的上下文（用于调试）
    if hasattr(response, "source_nodes") and response.source_nodes:
        print(f"\n[检索上下文] 共召回 {len(response.source_nodes)} 个相关片段:")
        for i, node in enumerate(response.source_nodes, 1):
            print(f"\n  [{i}] 相似度得分: {node.score:.4f}")
            print(f"      内容预览: {node.text[:150]}...")

except Exception as e:
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n[AI 调用] 调用失败！耗时: {duration:.2f} 秒")
    print(f"[错误信息] {type(e).__name__}: {e}")
    raise
