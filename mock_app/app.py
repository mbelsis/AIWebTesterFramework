from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import time

app = FastAPI(title="AI WebTester Demo App")
templates = Jinja2Templates(directory="mock_app/templates")

# In-memory store
class Employee(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: str
    created_at: float

EMPLOYEES: List[Employee] = []
NEXT_ID = 1
SESSION_COOKIE = "aiwt_session"

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
def login_view(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_post(username: str = Form(...), password: str = Form(...), domain: Optional[str] = Form(None)):
    # Accept any credentials; set cookie and redirect
    resp = RedirectResponse(url="/employees/new", status_code=303)
    resp.set_cookie(key=SESSION_COOKIE, value="ok", httponly=True)
    return resp

@app.get("/employees/new", response_class=HTMLResponse)
def employees_new(request: Request):
    # Check if logged in
    session = request.cookies.get(SESSION_COOKIE)
    if not session:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse("employees_new.html", {"request": request})

@app.post("/employees")
def create_employee(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...)
):
    global NEXT_ID
    employee = Employee(
        id=NEXT_ID,
        first_name=first_name,
        last_name=last_name,
        email=email,
        role=role,
        created_at=time.time()
    )
    EMPLOYEES.append(employee)
    NEXT_ID += 1
    
    return JSONResponse({
        "success": True,
        "message": f"Employee {first_name} {last_name} created successfully",
        "employee_id": employee.id
    })

@app.get("/api/employees")
def list_employees():
    return {"employees": [emp.dict() for emp in EMPLOYEES]}

@app.get("/health")
def health_check():
    return {"status": "ok", "total_employees": len(EMPLOYEES)}