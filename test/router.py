#####################################################
#                                                   #
#                  테스트 라우터 정의                  #
#                                                   #
#####################################################

from fastapi import APIRouter
from config.dependencies import (
    get_openai_client,
    get_langsmith_client
)
from fastapi import Depends, Body
from openai import AsyncOpenAI
from logs.logging_util import LoggerSingleton
import logging

# 로거 설정
logger = LoggerSingleton.get_logger(logger_name="test", level=logging.INFO)

router = APIRouter(prefix="/test")

@router.post("/test")
async def test(
    client: AsyncOpenAI = Depends(get_openai_client),
    prompt: str = Body(..., embed=True)
):
    logger.info("test")
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    logger.info(response.choices[0].message.content)
    return {"message": response.choices[0].message.content}