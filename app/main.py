from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.staticfiles import StaticFiles

from core.database import engine
from db.models import *
from api import auth, admin, warehouses, categories, items, cart, orders, suppliers, users, purchases, activity_logs

app = FastAPI()
app.state.limiter = auth.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mount("/images", StaticFiles(directory="images"), name="images")

import traceback
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("=== UNHANDLED EXCEPTION ===", file=sys.stderr)
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://185.61.77.236:3000", "http://185.61.77.236:1411"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(warehouses.router)
app.include_router(categories.router)
app.include_router(items.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(suppliers.router)
app.include_router(users.router)
app.include_router(purchases.router)
app.include_router(activity_logs.router)