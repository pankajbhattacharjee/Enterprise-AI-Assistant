# Architecture and operational notes

## Request flow

1. Streamlit obtains a JWT from FastAPI and sends it as a bearer token.
2. The chat endpoint stores the outcome and calls the manager.
3. The manager classifies the request into document, SQL, or hybrid.
4. The document agent retrieves only chunks owned by the requesting user, then grounds Gemini (or the offline fallback) with those chunks.
5. The SQL agent maps a small demo vocabulary to query templates, validates the statement, runs it, and returns rows.
6. A user can turn a response into a ReportLab PDF.

## Production replacements

The local vector store is deliberately dependency-light for a first run. Replace `LocalVectorStore` with a FAISS implementation that persists an index plus metadata, and substitute a Gemini embedding model or `sentence-transformers` vectors. The agent boundary remains unchanged.

For robust natural-language SQL generation, provide the LLM a curated schema and few-shot examples, parse the returned SQL with a SQL AST parser, enforce an allowlist of tables, issue queries through a read-only database role, set a statement timeout, and audit each execution. Never rely on prompt instructions for authorization.

## Firebase

Local JWT login is included so the demo has no cloud prerequisite. To use Firebase in a deployment, initialize `firebase_admin` with `FIREBASE_CREDENTIALS_PATH`, verify the client ID token at the API edge, then look up/provision the associated `User` record and issue the same short-lived internal token. This keeps Firebase identity management separate from application roles.

## Deployment checklist

- Set a long, unique `JWT_SECRET`, production `DATABASE_URL`, and restricted `CORS_ORIGINS`.
- Use a managed PostgreSQL database and a minimally privileged read-only account for SQL analytics.
- Put FastAPI behind a TLS reverse proxy, keep Streamlit internal if possible, and store uploads/reports in object storage.
- Run document indexing asynchronously, add rate limits, antivirus scanning, telemetry, error tracking, backups, and tenant isolation.
