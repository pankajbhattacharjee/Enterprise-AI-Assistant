import os
import httpx
import streamlit as st

st.set_page_config(page_title="Enterprise AI Assistant", page_icon="✦", layout="wide")
API_URL = st.sidebar.text_input("API URL", value=os.getenv("API_URL", "http://localhost:8000"))
st.title("✦ Enterprise AI Assistant")


def api(method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    if token := st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {token}"
    response = httpx.request(method, f"{API_URL}{path}", headers=headers, timeout=60, **kwargs)
    if response.is_error:
        raise RuntimeError(response.json().get("detail", response.text))
    return response


if "token" not in st.session_state:
    tab_login, tab_register = st.tabs(["Login", "Register"])
    with tab_login:
        with st.form("login"):
            email = st.text_input("Email"); password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                try: st.session_state.token = api("POST", "/api/auth/login", json={"email": email, "password": password}).json()["access_token"]; st.rerun()
                except Exception as exc: st.error(str(exc))
    with tab_register:
        with st.form("register"):
            email = st.text_input("Work email"); password = st.text_input("Password (8+ characters)", type="password")
            if st.form_submit_button("Create account"):
                try: st.session_state.token = api("POST", "/api/auth/register", json={"email": email, "password": password}).json()["access_token"]; st.rerun()
                except Exception as exc: st.error(str(exc))
    st.stop()

if st.sidebar.button("Log out"):
    del st.session_state.token; st.rerun()

tab_chat, tab_upload, tab_history = st.tabs(["Chat", "Upload", "History"])
with tab_chat:
    question = st.chat_input("Ask about your documents or sales data…")
    if question:
        try:
            with st.spinner("Routing your request…"):
                result = api("POST", "/api/chat", json={"question": question}).json()
            st.session_state.last_chat = {"question": question, "result": result}
            st.session_state.pop("report_pdf", None)
        except Exception as exc:
            st.error(str(exc))

    # A button click triggers a Streamlit rerun. Persisting the chat result
    # keeps it available for report generation after that rerun.
    if latest := st.session_state.get("last_chat"):
        result = latest["result"]
        with st.chat_message("user"):
            st.write(latest["question"])
        with st.chat_message("assistant"):
            st.write(result["answer"])
            if result.get("rows"):
                st.dataframe(result["rows"], use_container_width=True)
            if result.get("citations"):
                with st.expander("Sources"):
                    st.json(result["citations"])

        if st.button("Create PDF report", key="create_report"):
            try:
                report = api("POST", "/api/reports", json={
                    "question": latest["question"],
                    "answer": result["answer"],
                    "findings": [f"Intent: {result['intent']}"]
                }).json()
                st.session_state.report_pdf = api("GET", report["download_url"]).content
                st.success("PDF report created.")
            except Exception as exc:
                st.error(f"Could not create the PDF report: {exc}")

        if pdf := st.session_state.get("report_pdf"):
            st.download_button("Download PDF report", pdf, "enterprise-report.pdf", "application/pdf")
with tab_upload:
    upload = st.file_uploader("Upload PDF, DOCX or TXT", type=["pdf", "docx", "txt"])
    if upload and st.button("Index document"):
        try: st.success(api("POST", "/api/documents/upload", files={"file": (upload.name, upload.getvalue(), upload.type)}).json())
        except Exception as exc: st.error(str(exc))
with tab_history:
    try: st.dataframe(api("GET", "/api/history").json(), use_container_width=True)
    except Exception as exc: st.error(str(exc))
