import os
import yaml
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from qdrant_client import QdrantClient


# ----------------- 1. 加载配置文件 -----------------
def load_config(config_path="config.yaml"):
    """从 YAML 配置文件加载配置"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()

# ----------------- 2. 全局配置 -----------------
# 配置本地 Embedding 模型 (初次运行会自动从 HuggingFace 下载)
print("正在加载 Embedding 模型...")
Settings.embed_model = HuggingFaceEmbedding(
    model_name=config["embedding"]["model_name"]
)

# 配置 LLM (这里使用兼容 OpenAI 格式的 API，例如 DeepSeek)
llm_config = config["llm"]
Settings.llm = OpenAI(
    api_key=llm_config["api_key"],
    api_base=llm_config["api_base"],
    model=llm_config["model"],
)

# ----------------- 3. 连接向量数据库 -----------------
print("正在连接 Qdrant 数据库...")
vector_config = config["vector_store"]
client = QdrantClient(host=vector_config["host"], port=vector_config["port"])

# 创建 Qdrant 的 VectorStore 实例
# collection_name 可以看作是数据库里的一张表
vector_store = QdrantVectorStore(
    client=client, collection_name=vector_config["collection_name"]
)

# ----------------- 4. 加载文档并构建索引 -----------------
print("正在读取文档并建立索引...")
# 读取 data 目录下的所有文件
documents = SimpleDirectoryReader("./data").load_data()

# 将文档切块、向量化，并存入 Qdrant
index = VectorStoreIndex.from_documents(
    documents, vector_store=vector_store, show_progress=True
)

# ----------------- 5. 发起提问 (查询阶段) -----------------
print("\n--- 检索测试 ---")
# 将 Index 转换为一个查询引擎
query_engine = index.as_query_engine(
    similarity_top_k=config["query"]["similarity_top_k"]  # 召回最相关的 N 个分块
)

# 提问一个必须依赖外部知识才能回答的问题
question = "我们的内部图书馆管理系统使用了哪些数据库技术？"
print(f"User: {question}")

response = query_engine.query(question)
print(f"\nAI: {response.response}")
