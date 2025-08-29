from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from logs.logging_util import LoggerSingleton
from config.client import openai_client
from contextlib import asynccontextmanager
import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        r"""
 _____   ___   _____ __   __ _____  _____  _   _  _   _  _____  _____  _____   _____  _____   ___  ______  _____ 
|  ___| / _ \ /  ___|\ \ / //  __ \|  _  || \ | || \ | ||  ___|/  __ \|_   _| /  ___||_   _| / _ \ | ___ \|_   _|
| |__  / /_\ \\ `--.  \ V / | /  \/| | | ||  \| ||  \| || |__  | /  \/  | |   \ `--.   | |  / /_\ \| |_/ /  | |  
|  __| |  _  | `--. \  \ /  | |    | | | || . ` || . ` ||  __| | |      | |    `--. \  | |  |  _  ||    /   | |  
| |___ | | | |/\__/ /  | |  | \__/\\ \_/ /| |\  || |\  || |___ | \__/\  | |   /\__/ /  | |  | | | || |\ \   | |  
\____/ \_| |_/\____/   \_/   \____/ \___/ \_| \_/\_| \_/\____/  \____/  \_/   \____/   \_/  \_| |_/\_| \_|  \_/ 
"""
    )

    # Todo: 데이터베이스 초기화 로직 추가 필요
    # await to_thread(create_database_if_not_exists)
    # await init_db()
    # logger.info(
    #     f"\n{'=' * 80}\n"
    #     f"| {' ' * 29} 🛢️ DATABASE INITIATED 🛢️ {' ' * 29} |\n"
    #     f"{'=' * 80}\n"
    # )

    yield
    # 종료시 클린업 작업은 여기서
    # Todo: 데이터베이스 연결 해제 로직 추가 필요
    # Todo: 기타 리소스 정리 로직 추가 필요
    logger.info(
        r"""
 _____   ___   _____ __   __ _____  _____  _   _  _   _  _____  _____  _____   _____  _   _ ______ 
|  ___| / _ \ /  ___|\ \ / //  __ \|  _  || \ | || \ | ||  ___|/  __ \|_   _| |  ___|| \ | ||  _  \
| |__  / /_\ \\ `--.  \ V / | /  \/| | | ||  \| ||  \| || |__  | /  \/  | |   | |__  |  \| || | | |
|  __| |  _  | `--. \  \ /  | |    | | | || . ` || . ` ||  __| | |      | |   |  __| | . ` || | | |
| |___ | | | |/\__/ /  | |  | \__/\\ \_/ /| |\  || |\  || |___ | \__/\  | |   | |___ | |\  || |/ / 
\____/ \_| |_/\____/   \_/   \____/ \___/ \_| \_/\_| \_/\____/  \____/  \_/   \____/ \_| \_/|___/   
                                       🛑 ENGINE SHUTDOWN 🛑
    """
    )

# FastAPI 앱 인스턴스 생성
app = FastAPI(lifespan=lifespan)

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