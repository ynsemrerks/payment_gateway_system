from sqladmin import ModelView, Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from app.config import settings
from app.models.user import User
from app.models.transaction import Transaction
from app.models.idempotency import IdempotencyKey

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # Validate username/password
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            request.session.update({"token": "admin_token"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True

authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)

class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.email,
        User.balance,
        User.created_at,
    ]
    column_searchable_list = [User.email]
    column_sortable_list = [User.id, User.created_at, User.balance]
    icon = "fa-solid fa-user"
    name = "User"
    name_plural = "Users"

class TransactionAdmin(ModelView, model=Transaction):
    can_create = False
    column_list = [
        Transaction.id,
        Transaction.user_id,
        Transaction.type,
        Transaction.status,
        Transaction.amount,
        Transaction.created_at,
    ]
    column_searchable_list = [Transaction.idempotency_key, Transaction.bank_reference]
    column_sortable_list = [Transaction.created_at, Transaction.amount]
    column_filters = [Transaction.status, Transaction.type]
    icon = "fa-solid fa-money-bill-transfer"
    name = "Transaction"
    name_plural = "Transactions"


class IdempotencyKeyAdmin(ModelView, model=IdempotencyKey):
    can_create = False
    column_list = [
        IdempotencyKey.id,
        IdempotencyKey.user_id,
        IdempotencyKey.key,
        IdempotencyKey.response_status,
        IdempotencyKey.created_at,
    ]
    column_searchable_list = [IdempotencyKey.key]
    column_sortable_list = [IdempotencyKey.created_at, IdempotencyKey.response_status]
    icon = "fa-solid fa-key"
    name = "Idempotency Key"
    name_plural = "Idempotency Keys"

