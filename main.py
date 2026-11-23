import secrets                                     
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request               
from fastapi.staticfiles import StaticFiles

from auth import COOKIE_SECURE, SESSION_COOKIE    

from api.routes import router as api_router

from web.routes import router as web_router

from realtime.ws import router as websockets_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")   
async def session_cookie_for_everyone(request: Request, call_next):
    session_id = request.cookies.get(SESSION_COOKIE)
    is_new = not session_id
    if is_new:
        session_id = secrets.token_urlsafe(32)
    request.state.session_id = session_id
    response = await call_next(request)
    if is_new:
        response.set_cookie(key=SESSION_COOKIE, value=session_id,
                            httponly=True, samesite="lax", secure=COOKIE_SECURE)
    return response


app.include_router(api_router, prefix="/api")
app.include_router(web_router)
app.include_router(websockets_router, prefix="/ws")

app.mount("/static", StaticFiles(directory="static", html=True), name="static")
app.mount("/trivia", StaticFiles(directory="trivia/dist", html=True), name="trivia")





