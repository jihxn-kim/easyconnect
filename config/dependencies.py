#####################################################
#                                                   #
#                의존성 주입 함수 정의                 #
#                                                   #
#####################################################

from fastapi import Request

# Depends를 위한 헬퍼 함수
# openai
def get_openai_client(request: Request):
    return request.app.state.client_container.openai_client

# langsmith
def get_langsmith_client(request: Request):
    return request.app.state.client_container.langsmith_client