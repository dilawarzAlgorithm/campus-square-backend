from passlib.context import CryptContext
import re
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def extract_domain(email: str) -> str:
    match = re.search(r"@([\w.-]+)", email)
    if not match:
        raise ValueError("Invalid email format")
    return match.group(1).lower()

def generate_otp():
    return "".join(secrets.choice("0123456789") for _ in range(6))