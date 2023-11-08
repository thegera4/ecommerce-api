from typing import Optional, Type

from fastapi import FastAPI, Request
# response classes
from fastapi.responses import HTMLResponse
# templates
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from tortoise import BaseDBAsyncClient
from tortoise.contrib.fastapi import register_tortoise
# signals (used to perform some actions when a certain event occurs)
from tortoise.signals import post_save

from authentication import *
from emails import *
from models import *

# Run this command to start the server: uvicorn main:app --reload

app = FastAPI()


# post_save is a signal that is emitted after an object is saved
@post_save(User)
async def create_business(
        sender: "Type[User]",
        instance: User,
        created: bool,
        using_db: "Optional[BaseDBAsyncClient]",
        update_fields: List[str]
) -> None:
    if created:
        business_obj = await Business.create(name=instance.username, owner=instance)
        await business_pydantic.from_tortoise_orm(business_obj)
        await send_email([instance.email], instance)


@app.get("/")
def index():
    return {"message": "Hello World"}


@app.post("/registration")
async def user_registration(user: user_pydantic_in):
    user_info = user.dict(exclude_unset=True)
    user_info["password"] = get_hashed_password(user_info["password"])
    user_obj = await User.create(**user_info)
    new_user = await user_pydantic.from_tortoise_orm(user_obj)
    return {
        "status": "ok",
        "message": f"Hello {new_user.username}, thanks for choosing our services. Please check your email inbox to "
                   f"verify your account"
    }


templates = Jinja2Templates(directory="templates")


@app.get("/verification", response_class=HTMLResponse)
async def email_verification(request: Request, token: str):
    user = await verify_token(token)
    if user and not user.is_verified:
        user.is_verified = True
        await user.save()
        return templates.TemplateResponse("verification.html",
                                          {"request": request, "username": user.username,})
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )

register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True
)
