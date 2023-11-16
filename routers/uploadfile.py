from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from models import *
from dotenv import dotenv_values
from PIL import Image
import secrets

from routers.users import get_current_user

router = APIRouter(prefix="/uploadfile", tags=["Upload files"],
                   responses={status.HTTP_400_BAD_REQUEST: {"description": "Invalid file format"}})

# instance to access the environment variables
credentials = dotenv_values(".env")


# Endpoints:

# Upload user profile picture endpoint
@router.post("/profile", response_model=UploadProfilePicResponse, status_code=status.HTTP_200_OK)
async def upload_profile_picture(file: UploadFile = File(...), user: user_pydantic = Depends(get_current_user)):
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


# Upload product picture endpoint
@router.post("/product/{product_id}", response_model=UploadProductPicResponse, status_code=status.HTTP_200_OK)
async def upload_product_picture(file: UploadFile = File(...), product_id: int = None,
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
