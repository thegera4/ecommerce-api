from datetime import datetime
from typing import List
from pydantic import BaseModel
from tortoise import Model, fields
from tortoise.contrib.pydantic import pydantic_model_creator


# Tortoise ORM models
class User(Model):
    id = fields.IntField(pk=True, index=True)
    username = fields.CharField(max_length=20, null=False, unique=True)
    email = fields.CharField(max_length=200, null=False, unique=True)
    password = fields.CharField(max_length=100, null=False)
    is_verified = fields.BooleanField(default=False)
    join_date = fields.DatetimeField(default=datetime.utcnow)


# not used for one seller
# class Business(Model):
    # id = fields.IntField(pk=True, index=True)
    # name = fields.CharField(max_length=100, null=False, unique=True)
    # city = fields.CharField(max_length=100, null=False, default="Unspecified")
    # region = fields.CharField(max_length=100, null=False, default="Unspecified")
    # description = fields.TextField(null=True)
    # logo = fields.CharField(max_length=200, null=False, default="defaultBusiness.png")
    # owner = fields.ForeignKeyField('models.User', related_name='business')


class Product(Model):
    id = fields.IntField(pk=True, index=True)
    name = fields.CharField(max_length=100, null=False, index=True)
    image = fields.CharField(max_length=200, null=False, default="defaultProduct.png")
    original_price = fields.DecimalField(max_digits=12, decimal_places=2)
    category = fields.ForeignKeyField('models.Category', related_name='products')
    # new_price = fields.DecimalField(max_digits=12, decimal_places=2)
    # percentage_discount = fields.IntField()
    # offer_expiration_data = fields.DateField(default=datetime.utcnow)

    # date_published = fields.DatetimeField(default=datetime.utcnow)
    # business = fields.ForeignKeyField('models.Business', related_name='products')


class Category(Model):
    id = fields.IntField(pk=True, index=True)
    name = fields.CharField(max_length=30, null=False, unique=True)
    products: fields.ReverseRelation[Product]


# Pydantic models
user_pydantic = pydantic_model_creator(User, name="User", exclude=("is_verified",))
user_pydantic_in = pydantic_model_creator(User, name="UserIn", exclude_readonly=True, exclude=("is_verified",
                                                                                               "join_date"))
user_pydantic_out = pydantic_model_creator(User, name="UserOut", exclude=("password",))

# business_pydantic = pydantic_model_creator(Business, name="Business")
# business_pydantic_in = pydantic_model_creator(Business, name="BusinessIn", exclude=("id", "logo",))

product_pydantic = pydantic_model_creator(Product, name="Product")
product_pydantic_in = pydantic_model_creator(Product, name="ProductIn", exclude_readonly=True)

category_pydantic = pydantic_model_creator(Category, name="Category")
category_pydantic_in = pydantic_model_creator(Category, name="CategoryIn", exclude_readonly=True)


# Response models

# Products
class AllProductsResponse(BaseModel):
    status: str
    products: List[product_pydantic]


class SingleProductResponse(BaseModel):
    status: str
    data: product_pydantic


class AddProductResponse(BaseModel):
    status: str
    message: str
    product: product_pydantic


class DeleteProductResponse(BaseModel):
    status: str
    message: str


class UpdateProductResponse(BaseModel):
    status: str
    data: product_pydantic


# Users
class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class RegistrationResponse(BaseModel):
    status: str
    message: str


class AllUsersResponse(BaseModel):
    status: str
    users: List[user_pydantic_out]


class SingleUserResponse(BaseModel):
    status: str
    data: dict


# Upload files
class UploadProfilePicResponse(BaseModel):
    status: str
    message: str
    url: str


class UploadProductPicResponse(BaseModel):
    status: str
    message: str
    url: str


# Businesses
# class UpdateBusinessResponse(BaseModel):
    # status: str
    # data: business_pydantic


# Health check
class HealthCheckResponse(BaseModel):
    status: str
    message: str


# Categories
class AddCategoryResponse(BaseModel):
    status: str
    message: str
    category: category_pydantic


class AllCategoriesResponse(BaseModel):
    status: str
    categories: List[category_pydantic]
