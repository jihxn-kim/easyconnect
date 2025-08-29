from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
import logging
from logs.logging_util import LoggerSingleton
from config.client import openai_client

# FastAPI 앱 인스턴스 생성
app = FastAPI()

# Prometheus FastAPI 미들웨어 설정
Instrumentator().instrument(app).expose(app)

# # 라우터 등록
# routers = [document_router, TTS_router, trans_router, image_router, test_app_router, video_router, create_image_router, music_router]

# for router in routers:
#     app.include_router(router)

# 로거 설정
logger = LoggerSingleton.get_logger(logger_name="app", level=logging.INFO)

@app.post("/test")
async def test(
    prompt: str
):
    logger.info("test")
    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    logger.info(response.choices[0].message.content)
    return {"message": response.choices[0].message.content}