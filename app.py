# from dotenv import load_dotenv
# import os
# import certifi
# import json
# import uuid
# from pathlib import Path

# from fastapi import FastAPI, UploadFile, File, Form
# from fastapi.responses import StreamingResponse, JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# from langchain_core.messages import (
#     HumanMessage,
#     AIMessage,
#     AIMessageChunk,
#     ToolMessage,
# )

# from agent import get_agent
# from database import (
#     init_db,
#     save_chat_message,
#     get_chat_history,
#     create_or_update_conversation,
#     list_conversations,
# )
# from rag import add_document_to_rag
# from tools import set_current_thread_id


# # ENV


# load_dotenv()

# os.environ["SSL_CERT_FILE"] = certifi.where()
# os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Path("uploads").mkdir(exist_ok=True)
# Path("data").mkdir(exist_ok=True)

# init_db()



# # APP


# app = FastAPI(
#     title="Astr",
#     version="1.0.0"
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # REQUEST MODEL


# class ChatRequest(BaseModel):
#     message: str
#     thread_id: str
#     model: str = "gemini-2.5-flash"



# # HELPERS


# def sse_data(payload: dict) -> str:
#     return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# def should_stream_chunk(chunk, metadata) -> bool:
#     metadata = metadata or {}

#     node_name = str(
#         metadata.get("langgraph_node", "")
#     ).lower()

#     if "tool" in node_name:
#         return False

#     if isinstance(chunk, ToolMessage):
#         return False

#     if not isinstance(chunk, (AIMessage, AIMessageChunk)):
#         return False

#     if getattr(chunk, "tool_calls", None):
#         return False

#     if getattr(chunk, "invalid_tool_calls", None):
#         return False

#     additional_kwargs = (
#         getattr(chunk, "additional_kwargs", {}) or {}
#     )

#     if additional_kwargs.get("tool_calls"):
#         return False

#     return True


# def extract_text_from_chunk(chunk) -> str:
#     content = getattr(chunk, "content", "")

#     if not content:
#         return ""

#     if isinstance(content, str):
#         return content

#     if isinstance(content, list):
#         text_parts = []

#         for item in content:

#             if isinstance(item, str):
#                 text_parts.append(item)

#             elif isinstance(item, dict):

#                 if (
#                     item.get("type") == "text"
#                     and isinstance(item.get("text"), str)
#                 ):
#                     text_parts.append(item["text"])

#                 elif isinstance(item.get("text"), str):
#                     text_parts.append(item["text"])

#                 elif isinstance(item.get("content"), str):
#                     text_parts.append(item["content"])

#         return "".join(text_parts)

#     return ""


# # ROOT


# @app.get("/")
# async def root():
#     return {
#         "status": "running",
#         "service": "BappyGPT API"
#     }


# @app.get("/health")
# async def health():
#     return {"status": "ok"}



# # CONVERSATIONS


# @app.get("/conversations")
# async def conversations():
#     items = list_conversations()

#     return {
#         "conversations": [
#             {
#                 "thread_id": item.thread_id,
#                 "title": item.title,
#                 "created_at": item.created_at.isoformat(),
#                 "updated_at": item.updated_at.isoformat(),
#             }
#             for item in items
#         ]
#     }


# @app.get("/history/{thread_id}")
# async def history(thread_id: str):
#     messages = get_chat_history(thread_id)

#     return {
#         "messages": [
#             {
#                 "role": msg.role,
#                 "content": msg.content,
#             }
#             for msg in messages
#         ]
#     }



# # FILE UPLOAD


# @app.post("/upload")
# async def upload_document(
#     file: UploadFile = File(...),
#     thread_id: str = Form(...)
# ):
#     try:
#         allowed_extensions = [
#             ".pdf",
#             ".docx",
#             ".txt",
#             ".md",
#             ".py",
#             ".csv",
#         ]

#         filename = file.filename or "file"
#         suffix = Path(filename).suffix.lower()

#         if suffix not in allowed_extensions:
#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "success": False,
#                     "message": "Unsupported file type."
#                 },
#             )

#         file_id = str(uuid.uuid4())

#         file_path = (
#             f"uploads/{file_id}_"
#             f"{filename.replace(' ', '_')}"
#         )

#         with open(file_path, "wb") as f:
#             f.write(await file.read())

#         create_or_update_conversation(
#             thread_id,
#             "Uploaded document"
#         )

#         result = add_document_to_rag(
#             file_path=file_path,
#             thread_id=thread_id,
#         )

#         return {
#             "success": True,
#             "message": (
#                 f"Uploaded {result['filename']} "
#                 f"and created {result['chunks']} chunks."
#             ),
#         }

#     except Exception as e:
#         return JSONResponse(
#             status_code=500,
#             content={
#                 "success": False,
#                 "message": str(e),
#             },
#         )



# # CHAT STREAM


# @app.post("/chat/stream")
# async def chat_stream(payload: ChatRequest):

#     user_message = payload.message.strip()
#     thread_id = payload.thread_id
#     selected_model = payload.model

#     if not user_message:
#         return JSONResponse(
#             status_code=400,
#             content={
#                 "error": "Message is required."
#             },
#         )

#     create_or_update_conversation(
#         thread_id,
#         user_message,
#     )

#     save_chat_message(
#         thread_id,
#         "user",
#         user_message,
#     )

#     set_current_thread_id(thread_id)

#     agent = get_agent(selected_model)

#     config = {
#         "configurable": {
#             "thread_id": thread_id
#         }
#     }

#     def event_generator():
#         final_answer = ""

#         try:
#             inputs = {
#                 "messages": [
#                     HumanMessage(
#                         content=user_message
#                     )
#                 ]
#             }

#             for chunk, metadata in agent.stream(
#                 inputs,
#                 config=config,
#                 stream_mode="messages",
#             ):

#                 if not should_stream_chunk(
#                     chunk,
#                     metadata,
#                 ):
#                     continue

#                 token = extract_text_from_chunk(
#                     chunk
#                 )

#                 if token:
#                     final_answer += token

#                     yield sse_data({
#                         "token": token
#                     })

#             if final_answer.strip():
#                 save_chat_message(
#                     thread_id,
#                     "assistant",
#                     final_answer,
#                 )

#             yield sse_data({
#                 "done": True
#             })

#         except Exception as e:
#             yield sse_data({
#                 "error": str(e)
#             })

#             yield sse_data({
#                 "done": True
#             })

#     return StreamingResponse(
#         event_generator(),
#         media_type="text/event-stream",
#     )



# # MAIN

# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(
#         "app:app",
#         host="0.0.0.0",
#         port=8080,
#         reload=True,
#     )


from dotenv import load_dotenv
import os
import certifi
import json
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    AIMessageChunk,
    ToolMessage,
)

from agent import get_agent
from database import (
    init_db,
    save_chat_message,
    get_chat_history,
    create_or_update_conversation,
    list_conversations,
)
from rag import add_document_to_rag
from tools import set_current_thread_id


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

Path("uploads").mkdir(
    parents=True,
    exist_ok=True
)

Path("data").mkdir(
    parents=True,
    exist_ok=True
)

init_db()


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Astra",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# REQUEST MODELS
# =====================================================

class ChatRequest(BaseModel):
    message: str
    thread_id: str
    model: str = "gemini-2.5-flash"


# =====================================================
# HELPERS
# =====================================================

def sse_data(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def should_stream_chunk(chunk, metadata) -> bool:
    metadata = metadata or {}

    node_name = str(
        metadata.get("langgraph_node", "")
    ).lower()

    if "tool" in node_name:
        return False

    if isinstance(chunk, ToolMessage):
        return False

    if not isinstance(
        chunk,
        (AIMessage, AIMessageChunk)
    ):
        return False

    if getattr(chunk, "tool_calls", None):
        return False

    if getattr(
        chunk,
        "invalid_tool_calls",
        None
    ):
        return False

    additional_kwargs = (
        getattr(chunk, "additional_kwargs", {})
        or {}
    )

    if additional_kwargs.get("tool_calls"):
        return False

    return True


def extract_text_from_chunk(chunk) -> str:

    content = getattr(
        chunk,
        "content",
        ""
    )

    if not content:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        text_parts = []

        for item in content:

            if isinstance(item, str):
                text_parts.append(item)

            elif isinstance(item, dict):

                if (
                    item.get("type") == "text"
                    and isinstance(
                        item.get("text"),
                        str
                    )
                ):
                    text_parts.append(
                        item["text"]
                    )

                elif isinstance(
                    item.get("text"),
                    str
                ):
                    text_parts.append(
                        item["text"]
                    )

                elif isinstance(
                    item.get("content"),
                    str
                ):
                    text_parts.append(
                        item["content"]
                    )

        return "".join(text_parts)

    return ""


# =====================================================
# ROOT
# =====================================================

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "Astra API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }


# =====================================================
# CONVERSATIONS
# =====================================================

@app.get("/conversations")
async def conversations():

    items = list_conversations()

    return {
        "conversations": [
            {
                "thread_id": item.thread_id,
                "title": item.title,
                "created_at":
                    item.created_at.isoformat(),
                "updated_at":
                    item.updated_at.isoformat(),
            }
            for item in items
        ]
    }


@app.get("/history/{thread_id}")
async def history(thread_id: str):

    messages = get_chat_history(
        thread_id
    )

    return {
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in messages
        ]
    }


# =====================================================
# FILE UPLOAD
# =====================================================

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    thread_id: str = Form(...)
):
    try:

        allowed_extensions = [
            ".pdf",
            ".docx",
            ".txt",
            ".md",
            ".py",
            ".csv",
        ]

        filename = (
            file.filename
            or "file"
        )

        suffix = (
            Path(filename)
            .suffix
            .lower()
        )

        if suffix not in allowed_extensions:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message":
                        "Unsupported file type."
                }
            )

        file_id = str(
            uuid.uuid4()
        )

        file_path = (
            f"uploads/{file_id}_"
            f"{filename.replace(' ', '_')}"
        )

        with open(
            file_path,
            "wb"
        ) as f:
            f.write(
                await file.read()
            )

        create_or_update_conversation(
            thread_id,
            "Uploaded document"
        )

        result = add_document_to_rag(
            file_path=file_path,
            thread_id=thread_id
        )

        return {
            "success": True,
            "message":
                f"Uploaded "
                f"{result['filename']} "
                f"and created "
                f"{result['chunks']} chunks."
        }

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": str(e)
            }
        )


# =====================================================
# CHAT STREAM
# =====================================================

@app.post("/chat/stream")
async def chat_stream(
    payload: ChatRequest
):

    user_message = (
        payload.message.strip()
    )

    thread_id = payload.thread_id
    selected_model = payload.model

    if not user_message:
        return JSONResponse(
            status_code=400,
            content={
                "error":
                    "Message is required."
            }
        )

    create_or_update_conversation(
        thread_id,
        user_message[:100]
    )

    save_chat_message(
        thread_id,
        "user",
        user_message
    )

    set_current_thread_id(
        thread_id
    )

    agent = get_agent(
        selected_model
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    def event_generator():

        final_answer = ""

        try:

            inputs = {
                "messages": [
                    HumanMessage(
                        content=user_message
                    )
                ]
            }

            for chunk, metadata in agent.stream(
                inputs,
                config=config,
                stream_mode="messages",
            ):

                if not should_stream_chunk(
                    chunk,
                    metadata
                ):
                    continue

                token = (
                    extract_text_from_chunk(
                        chunk
                    )
                )

                if token:

                    final_answer += token

                    yield sse_data({
                        "token": token
                    })

            if final_answer.strip():

                save_chat_message(
                    thread_id,
                    "assistant",
                    final_answer
                )

            yield sse_data({
                "done": True
            })

        except Exception as e:

            yield sse_data({
                "error": str(e)
            })

            yield sse_data({
                "done": True
            })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":
                "no-cache",
            "Connection":
                "keep-alive",
        },
    )


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.getenv(
            "PORT",
            8080
        )
    )

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
    )
