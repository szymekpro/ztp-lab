from fastapi import FastAPI
from web.routes import router

app = FastAPI(title="Laboratorium 1 - REST API")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
