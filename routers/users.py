from fastapi import APIRouter, HTTPException, status, Depends
from models import User, user_pydantic, user_pydantic_in, Business
from fastapi.security import OAuth2PasswordBearer
import jwt
from dotenv import dotenv_values

router = APIRouter(prefix="/users", tags=["Users"], responses={status.HTTP_404_NOT_FOUND: {"description": "User(s) "
                                                                                                          "not "
                                                                                                          "found"}})

# instance to access the environment variables
credentials = dotenv_values(".env")

# create an instance for handling OAuth 2.0 bearer tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Auxiliary function to validate and get the information of a user
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


# Endpoints:

# Get all users endpoint
@router.get("/", response_model=dict, status_code=status.HTTP_200_OK)
async def get_all_users():
    try:
        users = await user_pydantic.from_queryset(User.all())
        if len(users) == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")
        return {"status": "ok", "users": users}
    except IndexError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Error retrieving users")


# Get single user endpoint
@router.post("/me", response_model=dict, status_code=status.HTTP_200_OK)
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
