from fastapi import APIRouter, HTTPException, status, Depends
from models import *
from routers.users import get_current_user


router = APIRouter(prefix="/products", tags=["Products"],
                   responses={status.HTTP_404_NOT_FOUND: {"description": "Product(s) not found"}})


# Endpoints:

# Get all products endpoint
@router.get("/", response_model=AllProductsResponse, status_code=status.HTTP_200_OK)
async def get_all_products():
    try:
        response = await product_pydantic.from_queryset(Product.all())
        return {"status": "ok", "products": response}
    except IndexError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found")


# Get a single product endpoint
@router.get("/{product_id}", response_model=SingleProductResponse, status_code=status.HTTP_200_OK)
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


# Add a single new product endpoint
@router.post("/", response_model=AddProductResponse, status_code=status.HTTP_200_OK)
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
            product_data = await product_pydantic.from_tortoise_orm(product_obj)
            # remove the image and date_published fields from the response
            product_data.pop("image")
            product_data.pop("date_published")
            return {"status": "ok", "message": "Product created successfully", "product": product_data}
        except ValueError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid data. Product not created in DB.")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid data. Original price must be > 0")


# Delete a single product endpoint
@router.delete("/{product_id}", response_model=DeleteProductResponse, status_code=status.HTTP_200_OK)
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


# Update a single product endpoint
@router.put("/{product_id}", response_model=UpdateProductResponse, status_code=status.HTTP_200_OK)
async def update_product(product_id: int, update_info: product_pydantic_in,
                         user: user_pydantic = Depends(get_current_user)):
    try:
        product = await Product.get(id=product_id)
        business = await product.business
        owner = await business.owner
        update_info = update_info.dict(exclude_unset=True)
        update_info["date_published"] = datetime.utcnow()
        if owner == user and update_info["original_price"] > 0:
            update_info["percentage_discount"] = round(
                (update_info["original_price"] - update_info["new_price"]) / update_info["original_price"] * 100)
            product = await product.update_from_dict(update_info)
            await product.save()
            response = await product_pydantic.from_tortoise_orm(product)
            return {"status": "ok", "data": response}
        else:
            if update_info["original_price"] <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid data. Original price must be > 0"
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to perform this action",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except IndexError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
