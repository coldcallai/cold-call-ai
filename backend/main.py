from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from router_auth import router as auth_router
from router_user import router as user_router
from router_team import router as team_router
from router_lead import router as lead_router
from router_task import router as task_router
from router_note import router as note_router
from router_call_log import router as call_log_router
from router_event import router as event_router
from router_agent import router as agent_router
from router_campaign import router as campaign_router
from router_script import router as script_router
from router_interaction import router as interaction_router

app = FastAPI(title="Dialgenix API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(team_router)
app.include_router(lead_router)
app.include_router(task_router)
app.include_router(note_router)
app.include_router(call_log_router)
app.include_router(event_router)
app.include_router(agent_router)
app.include_router(campaign_router)
app.include_router(script_router)
app.include_router(interaction_router)

@app.get("/")
def root():
    return {"status": "ok", "message": "Dialgenix API running"}
