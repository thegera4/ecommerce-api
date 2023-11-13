# Run this command to start the server: uvicorn main:app --reload
# Run this commando to freeze the requirements: pip freeze > requirements.txt

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

# Authentication
from authentication import *
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image

# Auxiliary functions
from emails import *
from models import *

app = FastAPI()

credentials = dotenv_values(".env")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# static file setup config
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return RedirectResponse(url="/docs")


# Token generation
@app.post("/token", response_model=dict, status_code=status.HTTP_200_OK)
async def generate_token(request_form: OAuth2PasswordRequestForm = Depends()):
    try:
        token = await token_generator(request_form.username, request_form.password)
        return {"access_token": token, "token_type": "bearer"}
    except IndexError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token not generated")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, credentials["SECRET"], algorithms=["HS256"])
        user = await User.get(id=payload.get("id"))
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return await user


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


# User email verification and authentication
@app.post("/users/me", response_model=dict, status_code=status.HTTP_200_OK)
async def user_login(user: user_pydantic_in = Depends(get_current_user)):
    try:
        business = await Business.get(owner=user)
        logo = business.logo
        logo_path = credentials["SERVER_URL"] + "/static/images/" + logo
        return {
            "status": "ok",
            "data": {
                "username": user.username,
                "email": user.email,
                "verified": user.is_verified,
                "joined_date": user.join_date.strftime("%b %d %Y"),
                "logo": logo_path
            }
        }
    except IndexError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@app.post("/registration", response_model=dict, status_code=status.HTTP_201_CREATED)
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


# Upload files operations
@app.post("/uploadfile/profile", response_model=dict, status_code=status.HTTP_200_OK)
async def create_upload_file(file: UploadFile = File(...), user: user_pydantic = Depends(get_current_user)):
    filepath = "./static/images/"
    filename = file.filename
    extension = filename.split(".")[1]

    if extension not in ["png", "jpg", "jpeg"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format")

    token_name = secrets.token_hex(10) + "." + extension
    generated_name = filepath + token_name

    try:
        file_content = await file.read()

        with open(generated_name, "wb") as file:
            file.write(file_content)

        # resize image *PILLOW*
        image = Image.open(generated_name)
        image = image.resize((200, 200))
        image.save(generated_name)
        file.close()

        business = await Business.get(owner=user)
        owner = await business.owner
        if owner == user:
            business.logo = token_name
            await business.save()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to perform this action",
                headers={"WWW-Authenticate": "Bearer"}
            )

        file_url = credentials["SERVER_URL"] + generated_name[1:]
        return {"status": "ok", "message": "Image uploaded successfully", "url": file_url}
    except IndexError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Image not uploaded due to an error")


@app.post("/uploadfile/product/{product_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def create_upload_file(file: UploadFile = File(...), product_id: int = None,
                             user: user_pydantic = Depends(get_current_user)):
    filepath = "./static/images/"
    filename = file.filename
    extension = filename.split(".")[1]

    if extension not in ["png", "jpg", "jpeg"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format")

    token_name = secrets.token_hex(10) + "." + extension
    generated_name = filepath + token_name

    try:
        file_content = await file.read()

        with open(generated_name, "wb") as file:
            file.write(file_content)

        # resize image *PILLOW*
        image = Image.open(generated_name)
        image = image.resize((200, 200))
        image.save(generated_name)
        file.close()

        product = await Product.get(id=product_id)
        business = await product.business
        owner = await business.owner

        if owner == user:
            product.image = token_name
            await product.save()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to perform this action",
                headers={"WWW-Authenticate": "Bearer"}
            )

        file_url = credentials["SERVER_URL"] + generated_name[1:]
        return {"status": "ok", "message": "Image uploaded successfully", "url": file_url}
    except IndexError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Image not uploaded due to an error")


# CRUD operations for products
@app.post("/products", response_model=product_pydantic, status_code=status.HTTP_201_CREATED)
async def add_new_product(product: product_pydantic_in, user: user_pydantic = Depends(get_current_user)):
    product_info = product.dict(exclude_unset=True)
    # avoid division by zero
    if product_info["original_price"] > 0:
        product_info["percentage_discount"] = round(
            (product_info["original_price"] - product_info["new_price"]) / product_info["original_price"] * 100)
        try:
            # create product in database
            product_obj = await Product.create(**product_info, business=user)
            # convert product object form database to pydantic model
            product_obj = await product_pydantic.from_tortoise_orm(product_obj)
            return {"status": "ok", "data": product_obj}
        except ValueError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid data. Product not created in DB.")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid data. Original price must be > 0")


@app.get("/products", response_model=list[product_pydantic], status_code=status.HTTP_200_OK)
async def get_products():
    try:
        response = await product_pydantic.from_queryset(Product.all())
        return {"status": "ok", "products": response}
    except IndexError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found")


@app.get("/products/{product_id}", response_model=product_pydantic, status_code=status.HTTP_200_OK)
async def get_product(product_id: int):
    try:
        product = await Product.get(id=product_id)
        business = await product.business
        owner = await business.owner
        response = await product_pydantic.from_queryset_single(Product.get(id=product_id))
        return {
            "status": "ok",
            "data": {
                "product_details": response,
                "business_details": {
                    "name": business.name,
                    "city": business.city,
                    "region": business.region,
                    "description": business.description,
                    "logo": business.logo,
                    "owner": owner.username,
                    "owner_email": owner.email,
                    "owner_id": owner.id,
                    "owner_joined_date": owner.join_date.strftime("%b %d %Y")
                }
            }
        }
    except IndexError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


@app.delete("/products/{product_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_product(product_id: int, user: user_pydantic = Depends(get_current_user)):
    try:
        product = await Product.get(id=product_id)
        business = await product.business
        owner = await business.owner
        if owner == user:
            await product.delete()
            return {"status": "ok", "message": "Product deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to perform this action",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except IndexError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True
)
