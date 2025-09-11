from fastapi import FastAPI, Request, Form, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid

app = FastAPI(title="Calendar Application")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Session storage (in production, use Redis or similar)
sessions = {}

# Data file paths
USERS_FILE = "data/users.json"
EVENTS_FILE = "data/events.json"

# Pydantic models
class User(BaseModel):
    id: int
    username: str
    password: str
    email: str
    full_name: str

class Event(BaseModel):
    id: Optional[int] = None
    user_id: int
    title: str
    description: str
    date: str
    time: str
    created_at: Optional[str] = None

class EventCreate(BaseModel):
    title: str
    description: str
    date: str
    time: str

# Helper functions
def load_users() -> List[Dict]:
    """Load users from JSON file"""
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_events() -> List[Dict]:
    """Load events from JSON file"""
    try:
        with open(EVENTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_events(events: List[Dict]):
    """Save events to JSON file"""
    with open(EVENTS_FILE, 'w') as f:
        json.dump(events, f, indent=2)

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user credentials"""
    users = load_users()
    for user in users:
        if user['username'] == username and user['password'] == password:
            return user
    return None

def get_current_user(request: Request) -> Optional[Dict]:
    """Get current user from session"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        return sessions[session_id]
    return None

def require_login(request: Request) -> Dict:
    """Dependency to require user login"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

def get_next_event_id() -> int:
    """Get the next available event ID"""
    events = load_events()
    if not events:
        return 1
    return max(event['id'] for event in events) + 1

# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - redirect to login or calendar"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/calendar", status_code=302)
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login form submission"""
    user = authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Invalid username or password"
        })
    
    # Create session
    session_id = str(uuid.uuid4())
    sessions[session_id] = user
    
    # Set cookie and redirect
    response = RedirectResponse(url="/calendar", status_code=302)
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response

@app.get("/logout")
async def logout(request: Request):
    """Handle user logout"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="session_id")
    return response

@app.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request, user: Dict = Depends(require_login)):
    """Display calendar page"""
    return templates.TemplateResponse("calendar.html", {
        "request": request,
        "user": user
    })

@app.get("/api/events")
async def get_events(request: Request, user: Dict = Depends(require_login)):
    """Get events for the current user"""
    events = load_events()
    user_events = [event for event in events if event['user_id'] == user['id']]
    return JSONResponse(content=user_events)

@app.get("/api/events/{year}/{month}")
async def get_events_by_month(year: int, month: int, request: Request, user: Dict = Depends(require_login)):
    """Get events for a specific month"""
    events = load_events()
    user_events = []
    
    for event in events:
        if event['user_id'] == user['id']:
            event_date = datetime.strptime(event['date'], '%Y-%m-%d')
            if event_date.year == year and event_date.month == month:
                user_events.append(event)
    
    return JSONResponse(content=user_events)

@app.post("/api/events")
async def create_event(event_data: EventCreate, request: Request, user: Dict = Depends(require_login)):
    """Create a new event"""
    events = load_events()
    
    new_event = {
        "id": get_next_event_id(),
        "user_id": user['id'],
        "title": event_data.title,
        "description": event_data.description,
        "date": event_data.date,
        "time": event_data.time,
        "created_at": datetime.now().isoformat()
    }
    
    events.append(new_event)
    save_events(events)
    
    return JSONResponse(content=new_event, status_code=201)

@app.put("/api/events/{event_id}")
async def update_event(event_id: int, event_data: EventCreate, request: Request, user: Dict = Depends(require_login)):
    """Update an existing event"""
    events = load_events()
    
    for i, event in enumerate(events):
        if event['id'] == event_id and event['user_id'] == user['id']:
            events[i].update({
                "title": event_data.title,
                "description": event_data.description,
                "date": event_data.date,
                "time": event_data.time
            })
            save_events(events)
            return JSONResponse(content=events[i])
    
    raise HTTPException(status_code=404, detail="Event not found")

@app.delete("/api/events/{event_id}")
async def delete_event(event_id: int, request: Request, user: Dict = Depends(require_login)):
    """Delete an event"""
    events = load_events()
    
    for i, event in enumerate(events):
        if event['id'] == event_id and event['user_id'] == user['id']:
            deleted_event = events.pop(i)
            save_events(events)
            return JSONResponse(content={"message": "Event deleted successfully"})
    
    raise HTTPException(status_code=404, detail="Event not found")

@app.get("/api/user")
async def get_current_user_info(request: Request, user: Dict = Depends(require_login)):
    """Get current user information"""
    return JSONResponse(content={
        "id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "full_name": user['full_name']
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)