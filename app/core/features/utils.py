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


def calculate_karma_tier(karma_points: int) -> dict:
    tiers = [
        {"min": 0, "max": 99, "level": 1, "title": "Novice"},
        {"min": 100, "max": 249, "level": 2, "title": "Contributor"},
        {"min": 250, "max": 499, "level": 3, "title": "Scholar"},
        {"min": 500, "max": float('inf'), "level": 4, "title": "Campus Legend"}
    ]
    
    current_tier = None
    next_tier = None
    
    for i, tier in enumerate(tiers):
        if tier["min"] <= karma_points <= tier["max"]:
            current_tier = tier
            if i + 1 < len(tiers):
                next_tier = tiers[i + 1]
            break
            
    if not current_tier:
        return {"level": 1, "title": "Novice", "progress_percentage": 0.0}
        
    result = {
        "level": current_tier["level"],
        "title": current_tier["title"],
    }
    
    if next_tier:
        result["next_tier_title"] = next_tier["title"]
        result["points_to_next"] = next_tier["min"] - karma_points
        range_size = current_tier["max"] - current_tier["min"] + 1
        points_in_tier = karma_points - current_tier["min"]
        result["progress_percentage"] = points_in_tier / range_size
    else:
        result["progress_percentage"] = 1.0
        
    return result