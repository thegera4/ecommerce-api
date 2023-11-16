# Run this command to start the server: uvicorn main:app --reload
# Run this command to freeze the requirements: pip freeze > requirements.txt
from typing import Optional, Type
from fastapi import FastAPI, Request, Depends

# response classes
from fastapi.responses import HTMLResponse

# templates
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from tortoise import BaseDBAsyncClient
from tortoise.contrib.fastapi import register_tortoise

# signals (used to perform some actions when a certain event occurs)
from tortoise.signals import post_save

# Authentication
from authentication import *
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles

# Auxiliary functions
from emails import *
from models import *

# routers
from routers import users, uploadfile, products, businesses

# Instance of fastapi
app = FastAPI()

# Routers
app.include_router(users.router)
app.include_router(products.router)
app.include_router(uploadfile.router)
app.include_router(businesses.router)

# Static files setup config
app.mount("/static", StaticFiles(directory="static"), name="static")

# Instance to access the environment variables
credentials = dotenv_values(".env")

# Instance for handling OAuth 2.0 bearer tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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


templates = Jinja2Templates(directory="templates")


@app.get("/")
def index():
    return RedirectResponse(url="/docs")


# Token generation endpoint
@app.post("/token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def generate_token(request_form: OAuth2PasswordRequestForm = Depends()):
    try:
        token = await token_generator(request_form.username, request_form.password)
        return {"access_token": token, "token_type": "bearer"}
    except IndexError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token not generated")


# User registration endpoint
@app.post("/registration", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def user_registration(user: user_pydantic_in):
    user_info = user.dict(exclude_unset=True)
    try:
        user_info["password"] = get_hashed_password(user_info["password"])
        user_obj = await User.create(**user_info)
        new_user = await user_pydantic.from_tortoise_orm(user_obj)
        return {
            "status": "ok",
            "message": f"Hello {new_user.username}, thanks for choosing our services. Please check your email inbox to "
                       f"verify your account"
        }
    except ValueError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid data. User not created in DB.")


# Email verification endpoint
@app.get("/verification", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def email_verification(request: Request, token: str):
    user = await verify_token(token)
    if user and not user.is_verified:
        user.is_verified = True
        await user.save()
        return templates.TemplateResponse("verification.html",
                                          {"request": request, "username": user.username, })
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
