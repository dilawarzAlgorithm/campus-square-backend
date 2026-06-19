from enum import Enum

class UserRole(str, Enum):
    STUDENT = "STUDENT"
    EMPLOYEE = "EMPLOYEE"
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