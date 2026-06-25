
# import streamlit as st
# import requests
# import json
# import uuid

# API_BASE_URL = "http://localhost:8000"



# # PAGE


# st.set_page_config(
#     page_title="Astra",
#     page_icon="🤖",
#     layout="wide"
# )


# # SESSION


# if "thread_id" not in st.session_state:
#     st.session_state.thread_id = str(uuid.uuid4())

# if "messages" not in st.session_state:
#     st.session_state.messages = []

# if "model" not in st.session_state:
#     st.session_state.model = "gemini-2.5-flash"



# # LOAD HISTORY


# def load_history(thread_id):
#     try:
#         response = requests.get(
#             f"{API_BASE_URL}/history/{thread_id}"
#         )

#         if response.status_code == 200:
#             data = response.json()

#             st.session_state.messages = (
#                 data.get("messages", [])
#             )

#     except Exception as e:
#         st.error(str(e))



# # SIDEBAR


# with st.sidebar:

#     st.title("Astra")

#     if st.button("➕ New Chat"):
#         st.session_state.thread_id = str(uuid.uuid4())
#         st.session_state.messages = []
#         st.rerun()

#     st.divider()

#     st.subheader("Model")

#     st.session_state.model = st.selectbox(
#         "Choose model",
#         [
#             "gemini-2.5-flash",
#             "gemini-2.5-pro",
#             "gemini-1.5-flash",
#             "gemini-1.5-pro"
#         ]
#     )

#     st.divider()

#     st.subheader("Upload Document")

#     uploaded_file = st.file_uploader(
#         "Upload",
#         type=[
#             "pdf",
#             "docx",
#             "txt",
#             "md",
#             "py",
#             "csv"
#         ]
#     )

#     if uploaded_file:

#         files = {
#             "file": (
#                 uploaded_file.name,
#                 uploaded_file,
#                 uploaded_file.type
#             )
#         }

#         data = {
#             "thread_id":
#             st.session_state.thread_id
#         }

#         with st.spinner("Uploading..."):

#             response = requests.post(
#                 f"{API_BASE_URL}/upload",
#                 files=files,
#                 data=data
#             )

#         if response.status_code == 200:
#             st.success(
#                 response.json()["message"]
#             )
#         else:
#             st.error(
#                 response.text
#             )

#     st.divider()

#     st.subheader("Conversations")

#     try:

#         response = requests.get(
#             f"{API_BASE_URL}/conversations"
#         )

#         if response.status_code == 200:

#             conversations = (
#                 response.json()
#                 .get("conversations", [])
#             )

#             for convo in conversations:

#                 if st.button(
#                     convo["title"][:30],
#                     key=convo["thread_id"]
#                 ):

#                     st.session_state.thread_id = (
#                         convo["thread_id"]
#                     )

#                     load_history(
#                         convo["thread_id"]
#                     )

#                     st.rerun()

#     except:
#         pass


# # HEADER


# st.title("Astra")

# st.caption(
#     f"Thread ID: {st.session_state.thread_id}"
# )


# # CHAT HISTORY


# for msg in st.session_state.messages:

#     role = msg["role"]

#     with st.chat_message(role):
#         st.markdown(msg["content"])


# # CHAT INPUT


# prompt = st.chat_input(
#     "Ask anything..."
# )

# if prompt:

#     st.session_state.messages.append(
#         {
#             "role": "user",
#             "content": prompt
#         }
#     )

#     with st.chat_message("user"):
#         st.markdown(prompt)

#     with st.chat_message("assistant"):

#         placeholder = st.empty()

#         full_response = ""

#         payload = {
#             "message": prompt,
#             "thread_id":
#                 st.session_state.thread_id,
#             "model":
#                 st.session_state.model
#         }

#         try:

#             response = requests.post(
#                 f"{API_BASE_URL}/chat/stream",
#                 json=payload,
#                 stream=True
#             )

#             for line in response.iter_lines():

#                 if not line:
#                     continue

#                 decoded = (
#                     line.decode("utf-8")
#                     .strip()
#                 )

#                 if not decoded.startswith(
#                     "data:"
#                 ):
#                     continue

#                 data = decoded[5:].strip()

#                 try:

#                     event = json.loads(data)

#                     if "token" in event:

#                         full_response += (
#                             event["token"]
#                         )

#                         placeholder.markdown(
#                             full_response
#                         )

#                     if event.get("done"):
#                         break

#                 except:
#                     continue

#         except Exception as e:

#             full_response = (
#                 f"Error: {str(e)}"
#             )

#             placeholder.error(
#                 full_response
#             )

#     st.session_state.messages.append(
#         {
#             "role": "assistant",
#             "content": full_response
#         }
#     )

import os
import json
import uuid
import requests
import streamlit as st


# =====================================================
# CONFIG
# =====================================================

API_BASE_URL = "https://agentic-ai-chat-bot-1.onrender.com"


st.set_page_config(
    page_title="Astra",
    page_icon="🤖",
    layout="wide"
)


# =====================================================
# SESSION STATE
# =====================================================

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(
        uuid.uuid4()
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "model" not in st.session_state:
    st.session_state.model = (
        "gemini-2.5-flash"
    )


# =====================================================
# API HELPERS
# =====================================================

def load_history(thread_id: str):
    try:

        response = requests.get(
            f"{API_BASE_URL}/history/{thread_id}",
            timeout=30
        )

        if response.status_code == 200:

            data = response.json()

            st.session_state.messages = (
                data.get(
                    "messages",
                    []
                )
            )

    except Exception as e:

        st.error(
            f"Failed to load history: {e}"
        )


def get_conversations():

    try:

        response = requests.get(
            f"{API_BASE_URL}/conversations",
            timeout=30
        )

        if response.status_code == 200:

            return (
                response.json()
                .get(
                    "conversations",
                    []
                )
            )

    except Exception:
        pass

    return []


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title("🤖 Astra")

    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        st.session_state.thread_id = (
            str(uuid.uuid4())
        )

        st.session_state.messages = []

        st.rerun()

    st.divider()

    st.subheader("Model")

    models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]

    current_index = (
        models.index(
            st.session_state.model
        )
        if st.session_state.model
        in models
        else 0
    )

    st.session_state.model = (
        st.selectbox(
            "Choose model",
            models,
            index=current_index
        )
    )

    st.divider()

    st.subheader(
        "📄 Upload Document"
    )

    uploaded_file = (
        st.file_uploader(
            "Upload a file",
            type=[
                "pdf",
                "docx",
                "txt",
                "md",
                "py",
                "csv",
            ]
        )
    )

    if uploaded_file:

        files = {
            "file": (
                uploaded_file.name,
                uploaded_file,
                uploaded_file.type
            )
        }

        data = {
            "thread_id":
                st.session_state.thread_id
        }

        try:

            with st.spinner(
                "Uploading..."
            ):

                response = requests.post(
                    f"{API_BASE_URL}/upload",
                    files=files,
                    data=data,
                    timeout=300
                )

            if response.status_code == 200:

                st.success(
                    response.json()[
                        "message"
                    ]
                )

            else:

                st.error(
                    response.text
                )

        except Exception as e:

            st.error(
                f"Upload failed: {e}"
            )

    st.divider()

    st.subheader(
        "💬 Conversations"
    )

    conversations = (
        get_conversations()
    )

    for convo in conversations[:50]:

        title = (
            convo["title"][:40]
            if convo["title"]
            else "New Chat"
        )

        if st.button(
            title,
            key=convo["thread_id"],
            use_container_width=True
        ):

            st.session_state.thread_id = (
                convo["thread_id"]
            )

            load_history(
                convo["thread_id"]
            )

            st.rerun()


# =====================================================
# HEADER
# =====================================================

st.title("🤖 Astra")

st.caption(
    f"Thread ID: "
    f"{st.session_state.thread_id}"
)


# =====================================================
# CHAT HISTORY
# =====================================================

for msg in st.session_state.messages:

    with st.chat_message(
        msg["role"]
    ):
        st.markdown(
            msg["content"]
        )


# =====================================================
# CHAT INPUT
# =====================================================

prompt = st.chat_input(
    "Ask anything..."
)

if prompt:

    user_message = {
        "role": "user",
        "content": prompt
    }

    st.session_state.messages.append(
        user_message
    )

    with st.chat_message(
        "user"
    ):
        st.markdown(prompt)

    with st.chat_message(
        "assistant"
    ):

        placeholder = st.empty()

        full_response = ""

        payload = {
            "message": prompt,
            "thread_id":
                st.session_state.thread_id,
            "model":
                st.session_state.model,
        }

        try:

            response = requests.post(
                f"{API_BASE_URL}/chat/stream",
                json=payload,
                stream=True,
                timeout=300,
            )

            if response.status_code != 200:

                raise Exception(
                    response.text
                )

            for line in (
                response.iter_lines()
            ):

                if not line:
                    continue

                decoded = (
                    line.decode(
                        "utf-8"
                    ).strip()
                )

                if not decoded.startswith(
                    "data:"
                ):
                    continue

                try:

                    event = json.loads(
                        decoded[5:].strip()
                    )

                    if (
                        "token"
                        in event
                    ):

                        full_response += (
                            event["token"]
                        )

                        placeholder.markdown(
                            full_response
                        )

                    if (
                        "error"
                        in event
                    ):

                        raise Exception(
                            event["error"]
                        )

                    if event.get(
                        "done"
                    ):
                        break

                except json.JSONDecodeError:
                    continue

        except Exception as e:

            full_response = (
                f"❌ Error: {e}"
            )

            placeholder.error(
                full_response
            )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response,
        }
    )