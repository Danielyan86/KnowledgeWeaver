# KnowledgeWeaver

知识图谱 + RAG 混合问答系统

中文 | [English](README.md)

## 项目简介

KnowledgeWeaver 是一个结合了知识图谱（Knowledge Graph）和检索增强生成（RAG）技术的智能问答系统。系统能够从文档中自动提取实体和关系，构建知识图谱，并通过向量检索和图谱推理相结合的方式，提供准确、有上下文的问答服务。

## 核心功能

- **文档处理**：支持 PDF 和 TXT 格式文档的自动解析和分块
- **知识提取**：基于 LLM 的实体和关系抽取
- **知识图谱**：自动构建、规范化和存储知识图谱
- **混合检索**：结合向量相似度检索和图谱结构检索
- **智能问答**：基于检索结果的上下文感知问答
- **可视化**：基于 D3.js 的交互式知识图谱可视化

## 系统架构

![系统架构图](docs/architecture-cn.png)

### 处理流程

1. **输入层**：接收文档（txt/pdf）
2. **处理层**：
   - 文档分块
   - LLM 实体和关系提取
   - 知识合并和规范化
3. **存储层**：
   - JSON 文件存储
   - ChromaDB 向量数据库
4. **服务层**：
   - FastAPI 后端服务
   - 混合检索器
   - QA 引擎
5. **前端层**：
   - D3.js 知识图谱可视化
   - 聊天问答界面

## 技术栈

### 后端
- **FastAPI**：高性能 Web 框架
- **OpenAI**：LLM 集成
- **ChromaDB**：向量数据库
- **Jinja2**：提示词模板引擎

### 前端
- **D3.js**：知识图谱可视化
- **JavaScript**：交互逻辑

### 外部服务
- **LLM API**：space.ai-builders.com

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件并配置：

```bash
LLM_BINDING_HOST=https://space.ai-builders.com/backend/v1
LLM_BINDING_API_KEY=your_api_key_here
```

### 启动服务

```bash
cd backend
python server.py
```

### 处理文档

```bash
python backend/process_book.py
```

## 项目结构

```
KnowledgeWeaver/
├── backend/              # 后端代码
│   ├── server.py        # FastAPI 服务
│   ├── extractor.py     # 知识提取
│   ├── hybrid_retriever.py  # 混合检索器
│   ├── qa_engine.py     # 问答引擎
│   ├── vector_store.py  # 向量存储
│   ├── embedder.py      # 文本嵌入
│   └── prompts/         # 提示词模板
├── frontend/            # 前端代码
│   ├── kg-config.js     # 图谱配置
│   └── kg-normalizer.js # 图谱规范化
├── rag_storage/         # RAG 存储目录
├── data/                # 数据目录
├── docs/                # 文档
│   ├── architecture-cn.png      # 架构图（中文）
│   ├── architecture-en.png      # 架构图（英文）
│   ├── architecture-diagram-cn.html  # 交互式架构图（中文）
│   └── architecture-diagram-en.html  # 交互式架构图（英文）
└── tests/               # 测试用例
```

## 主要特性

### 知识图谱规范化
- 实体去重和合并
- 关系标准化
- 信息孤岛检测和连接

### 混合检索策略
- 向量相似度检索（RAG）
- 图谱结构检索（KG）
- 动态权重融合

### 智能问答
- 上下文感知
- 多源信息整合
- 结构化答案生成

## 许可证

MIT License
