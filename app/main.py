from fastapi import FastAPI

app = FastAPI(title="FastAPI Docker App")

@app.get("/")
async def root():
    return {"message": "Оно живое"}