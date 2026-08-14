from enum import Enum

class UserRole(str, Enum):
    STUDENT = "STUDENT"
    COMMUNITY_HEAD = "COMMUNITY_HEAD"
    ADMIN = "ADMIN"

class ResourceType(str, Enum):
    PYQ = "PYQ"
    NOTE = "NOTE"
    SYLLABUS = "SYLLABUS"
    OTHER = "OTHER"

class VoteType(str, Enum):
    UPVOTE = "UPVOTE"
    DOWNVOTE = "DOWNVOTE"

class Semester(int, Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8

class SquareCategory(str, Enum):
    NOTICE = "NOTICE"
    ROOMMATE = "ROOMMATE"
    RIDE_POOL = "RIDE_POOL"
    LOST_FOUND = "LOST_FOUND"
    EVENT = "EVENT"
    COMPLAINT = "COMPLAINT"
    RANDOM = "RANDOM"

class BazaarCategory(str, Enum):
    TEXTBOOK = "TEXTBOOK"
    ELECTRONICS = "ELECTRONICS"
    FURNITURE = "FURNITURE"
    CLOTHING = "CLOTHING"
    STATIONERY = "STATIONERY"
    OTHER = "OTHER"

class ItemCondition(str, Enum):
    NEW = "NEW"
    LIKE_NEW = "LIKE_NEW"
    GOOD = "GOOD"
    FAIR = "FAIR"

class HubPrivacy(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    INVITE_ONLY = "INVITE_ONLY"