from enum import Enum

class UserRole(str, Enum):
    STUDENT = "STUDENT"
    EMPLOYEE = "EMPLOYEE"
    COMMUNITY_HEAD = "COMMUNITY_HEAD"
    ADMIN = "ADMIN"