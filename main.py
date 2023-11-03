from fastapi import FastAPI
from starlette.responses import RedirectResponse
from tortoise.contrib.fastapi import register_tortoise
from models import *
from authentication import *
# signals are used to perform some actions when a certain event occurs
# signals
from tortoise.signals import post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient

# Run this command to start the server:
# uvicorn main:app --reload


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
        # TODO: send the email to the user


@app.get("/")
def index():
    return RedirectResponse(url="/docs")


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


register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True
)
