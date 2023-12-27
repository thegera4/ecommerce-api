from fastapi import APIRouter, HTTPException, status, Depends
from models import *


router = APIRouter(prefix="/categories", tags=["Categories"],
                   responses={status.HTTP_404_NOT_FOUND: {"description": "Category(s) not found"}})


# Endpoints:

# Add a new category endpoint
@router.post("/", response_model=AddCategoryResponse, status_code=status.HTTP_200_OK)
async def add_new_category(category: category_pydantic_in):
    category_info = category.dict(exclude_unset=True)
    try:
        # create category in database
        category_obj = await Category.create(**category_info)
        # convert category object form database to pydantic model
        category_data = await category_pydantic.from_tortoise_orm(category_obj)
        return {"status": "ok", "message": "Category created successfully", "category": category_data}
    except ValueError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid data. Category not created!.")


# Get all categories endpoint
@router.get("/", response_model=AllCategoriesResponse, status_code=status.HTTP_200_OK)
async def get_all_categories():
    try:
        response = await category_pydantic.from_queryset(Category.all())
        return {"status": "ok", "categories": response}
    except IndexError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No categories found")
