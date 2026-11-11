from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.meetings import router

app = FastAPI(title="Event Sync Service", version="1.0.0",
              description="Reconciles CRM and Calendar meeting records.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

@app.get("/health")
def health():
    return {"status":"ok"}
