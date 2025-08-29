from langsmith import Client as LangSmithClient
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# 클라이언트 설정
langsmith_client = LangSmithClient()
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
