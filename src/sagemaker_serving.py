import asyncio
import os
import sys
import time
import uvicorn
from typing import Optional
from pydantic import ValidationError

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, Response, StreamingResponse

from vllm.entrypoints.openai.api_server import app as api_app, parse_args, logger
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.entrypoints.openai.serving_chat import OpenAIServingChat
from vllm.entrypoints.openai.serving_completion import OpenAIServingCompletion
from vllm.entrypoints.openai.serving_embedding import OpenAIServingEmbedding
from vllm.entrypoints.openai.protocol import (ChatCompletionRequest,
                                              ChatCompletionResponse, ErrorResponse)

instance_to_gpus = {
    "ml.g5.4xlarge": 1,    # A10G （24 GB）
    "ml.g6.4xlarge": 1,    # L4 （24 GB）
    "ml.g5.12xlarge": 4,   # A10G （24 GB * 4）
    "ml.g6.12xlarge": 4,   # L4（24 GB * 4）
    "ml.g5.48xlarge": 8,   # A10G（24 GB * 8）
    "ml.g6.48xlarge": 8,   # L4 （24 GB * 4）
    "ml.p4d.24xlarge": 8,  # A100 （40 GB * 8）
    "ml.p4de.24xlarge": 8,  # A100 （80 GB * 8）
    "ml.p5.48xlarge": 8,   # H100 （80 GB * 8）
}

def get_num_gpus(instance_type):
    try:
        return instance_to_gpus[instance_type]
    except KeyError:
        raise ValueError(f"Instance type {instance_type} not found in the dictionary")


app = FastAPI()

# Merge routes form api_app to app
# Note! The sagemaker model server only 
# recognizes /ping and /invocations API, 
# so this won't work.
for route in api_app.routes:
    app.router.routes.append(route)

# As sagemaker endpoint requires...
@app.get("/ping")
def ping():
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)

# As sagemaker endpoint requires...
@app.post("/invocations")
# @measure_time
async def invocations(request: Request):
    try:
        payload = await request.json()
        chat_completion_request = ChatCompletionRequest(**payload)
    except ValidationError as e:
        return JSONResponse(content={"error": "Invalid request format", "details": e.errors()}, status_code=400)

    generator = await openai_serving_chat.create_chat_completion(
        chat_completion_request, request)
    if isinstance(generator, ErrorResponse):
        return JSONResponse(content=generator.model_dump(),
                            status_code=generator.code)
    
    if 'stream' in payload and payload['stream']:
        return StreamingResponse(content=generator,
                                 media_type="text/event-stream")
    else:
        assert isinstance(generator, ChatCompletionResponse)
        return JSONResponse(content=generator.model_dump())

def start_api_server():
    # Get args from Envs.
    args = parse_args()
    args.host = os.getenv('API_HOST', '0.0.0.0')
    args.port = int(os.getenv('API_PORT', 8000))
    args.model = os.getenv('MODEL_ID', None)
    args.tensor_parallel_size = get_num_gpus(os.getenv('INSTANCE_TYPE'))
    args.uvicorn_log_level = os.getenv('UVICORN_LOG_LEVEL', 'info')

    if args.model is None:
        sys.exit("MODEL_ID must be provided")
    
    logger.info(f"Starting sagemaker vllm  with args: {args}")

    # Below code is adpated from: vllm/entrypoints/openai/api_server.py

    if args.served_model_name is not None:
        served_model_names = args.served_model_name
    else:
        served_model_names = [args.model]

    engine_args = AsyncEngineArgs.from_cli_args(args)
    global engine
    engine = AsyncLLMEngine.from_engine_args(engine_args)

    event_loop: Optional[asyncio.AbstractEventLoop]
    try:
        event_loop = asyncio.get_running_loop()
    except RuntimeError:
        event_loop = None

    if event_loop is not None and event_loop.is_running():
        # If the current is instanced by Ray Serve,
        # there is already a running event loop
        model_config = event_loop.run_until_complete(engine.get_model_config())
    else:
        # When using single vLLM without engine_use_ray
        model_config = asyncio.run(engine.get_model_config())
        
    global openai_serving_chat, openai_serving_completion, openai_serving_embedding
    openai_serving_chat = OpenAIServingChat(engine, model_config,
                                            served_model_names,
                                            args.response_role,
                                            args.lora_modules,
                                            args.chat_template)
    # Not supported now.
    # openai_serving_completion = OpenAIServingCompletion(
    #     engine, model_config, served_model_names, args.lora_modules)
    # openai_serving_embedding = OpenAIServingEmbedding(engine, model_config,
    #                                                   served_model_names)
    
    # Spin up the API server
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.uvicorn_log_level)

if __name__ == "__main__":
    start_api_server()
