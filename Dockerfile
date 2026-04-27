# llm_image/Dockerfile
# Build context is llm_image/ (self-contained, no files from outside):
#   docker build -t agentic-llm-svc:latest llm_image/
FROM python:3.14-slim

WORKDIR /app

# 安裝系統依賴與 Node.js (供 LLM CLI 工具使用)
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# 全域安裝 LLM CLI 工具
RUN npm install -g @anthropic-ai/claude-code
RUN npm install -g @google/gemini-cli
RUN npm install -g @openai/codex
RUN npm install -g opencode-ai

# 安裝 Python 依賴
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 複製 llm_agent package（llm_target + llm_svc）
COPY llm_agent/ ./llm_agent/

# 複製 FastAPI app
COPY main.py ./main.py

EXPOSE 7206

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7206"]
