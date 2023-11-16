from fastapi import APIRouter, HTTPException, status, Depends
from models import *
from routers.users import get_current_user


router = APIRouter(prefix="/businesses", tags=["Businesses"],
                   responses={status.HTTP_404_NOT_FOUND: {"description": "Business(es) not found"}})

# Endpoints:


# Update a single business endpoint
@router.put("/{business_id}", response_model=UpdateBusinessResponse, status_code=status.HTTP_200_OK)
async def update_business(business_id: int, business_info: business_pydantic_in,
                          user: user_pydantic = Depends(get_current_user)):
    business_info = business_info.dict()
    try:
        business = await Business.get(id=business_id)
        owner = await business.owner
        if owner == user:
            await business.update_from_dict(business_info)
            await business.save()
            response = await business_pydantic.from_tortoise_orm(business)
            return {"status": "ok", "data": response}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to perform this action",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except IndexError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")