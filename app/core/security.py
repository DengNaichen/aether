import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.config import settings
from app.models.user import User

# set hashed context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# jwt configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
REFRESH_TOKEN_EXPIRE_DAY = settings.REFRESH_TOKEN_EXPIRE_DAYS
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def get_password_hash(password: str) -> str:
    """
    hash a plaintext password

    Args:
        password (str): password to hash

    Returns:
        str: hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    verify if the plain password matches the hashed password

    Args:
        plain_password (str): plain password to verify
        hashed_password (str): hashed password to verify

    Returns:
        bool: True if the password matches the hashed password
        False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user: User, expires_delta: timedelta | None = None) -> str:
    """
    Generate a JWT access token for a given user

    This function creates a signed JWT containing the user's ID,
    admin status, issued-at time, and expiration time. The expiration
    time can be customized via `expires_delta` or default to the
    configured `REFRESH_TOKEN_EXPIRE_DAYS` environment variable.

    Args:
        user(User): The user object for whom the access token is created.
        expires_delta (timedelta | None, optional): The time duration after
            which the access token will expire. If not provided, a default
            duration is applied.

    Returns:
        str: The encoded JWT access token.

    Example:
        >>> token = create_access_token(user)
        >>> print(token)
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "exp": expire,
        "sub": str(user.id),
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
        "is_admin": user.is_admin,
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_refresh_token(user: User) -> str:
    """
    Generate a JWT refresh token for a given user

    This function creates a signed refresh token can be used to obtain
    new access tokens with requiring the user to log in again. The token
    includes the user's ID, a unique identifier(JTI), issued-at time,
    and an expiration date based on the configured `REFRESH_TOKEN_EXPIRE_DAYS`

    Args:
        user(User): The user object for whom the refresh token is created.

    Returns:
        str: The encoded JWT refresh token.

    Example:
        >>> token = create_refresh_token(user)
        >>> print(token)
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAY)
    to_encode = {
        "exp": expires,
        "sub": str(user.id),
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    encode_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


async def authenticate_user(
    db: AsyncSession, email: EmailStr, password: str
) -> User | None:
    """
    Authenticate a user with the given email and password.

    This asynchronous function retrieves the user from the database by email,
    verifies that the user exists and is active, and checks whether the
    provided password matches the stored hashed password. Returns the user
    object if authentication is successful; otherwise, returns None.

    Args:
        db (AsyncSession): SQLAlchemy asynchronous database session.
        email (EmailStr): Email address of the user.
        password (str): Plain-text password provided by the user.

    Returns:
        User | None: The authenticated user object if credentials are valid;
            otherwise, None.

    Example:
        >>> async def demo():
        ...     exp_em = EmailStr("example@email")
        ...     exp_user = await authenticate_user(db, email=exp_em, password="p")
        ...     if user:
        ...         print(user.id)
        ...     else:
        ...         print("Invalid credentials")
    """
    user = await crud.user.get_user_by_email(db, email=email)

    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def generate_reset_token() -> str:
    """
    Generate a cryptographically secure random token for password reset.

    Returns:
        str: A 32-character URL-safe token

    Example:
        >>> token = generate_reset_token()
        >>> print(token)
        'k7j9m2n4p6q8r0s1t3u5v7w9x1y3z5'
    """
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    """
    Hash a reset token using SHA-256 for fast, secure database lookups.

    We use SHA-256 instead of bcrypt to enable direct database lookups
    while still protecting tokens if the database is compromised.

    Why SHA-256 is safe here:
    - Reset tokens have 256 bits of cryptographic randomness
    - Impossible to reverse or brute-force
    - Allows O(1) database lookups vs O(n) with bcrypt

    Args:
        token (str): The plain reset token from secrets.token_urlsafe(32)

    Returns:
        str: SHA-256 hex digest (64 characters)

    Example:
        >>> token = "VGhpcyBpcyBhIHRlc3Q"
        >>> hashed = hash_reset_token(token)
        >>> print(len(hashed))
        64
        >>> # Store: user.reset_token = hashed
        >>> # Lookup: WHERE reset_token = hash_reset_token(input)
    """
    import hashlib

    return hashlib.sha256(token.encode()).hexdigest()
