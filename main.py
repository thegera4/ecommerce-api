from fastapi import FastAPI
from starlette.responses import RedirectResponse
from tortoise.contrib.fastapi import register_tortoise
from models import *

# Run this command to start the server:
# uvicorn main:app --reload

app = FastAPI()


@app.get("/")
def index():
    return RedirectResponse(url="/docs")


register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True
)
