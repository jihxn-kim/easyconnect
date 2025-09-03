#####################################################
#                                                   #
#                앱 상태 정의 및 관리                  #
#                                                   #
#####################################################

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from logs.logging_util import LoggerSingleton
from contextlib import asynccontextmanager
from config.clients import initialize_clients
from test.router import router as test_router
from tools.notion.OAuth import router as notion_oauth_router
from tools.notion.webhook import router as notion_webhook_router
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

    # 앱 상테에 클라이언트 컨테이너를 저장할 객체 초기화
    global client_container
    client_container = initialize_clients()
    app.state.client_container = client_container

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

# 라우터 등록
routers = [test_router, notion_oauth_router, notion_webhook_router]

for router in routers:
    app.include_router(router)

# 라우터에 client_container 전달은 app.state를 통해 처리합니다.

# 로거 설정
logger = LoggerSingleton.get_logger(logger_name="app", level=logging.INFO)