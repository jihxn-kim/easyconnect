from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
import logging
from logs.logging_util import LoggerSingleton

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
async def test():
    logger.info("test")
    return {"message": "Hello, World!"}