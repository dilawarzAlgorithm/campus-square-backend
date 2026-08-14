from app.core.database.database import Base

from app.models.registration import Institution, User, Profile, RefreshToken
from app.models.vault import Department, AcademicResource, ResourceVote, SavedResource
from app.models.square import Notice, NoticeComment, NoticeVote
from app.models.chat import Conversation, ConversationParticipant, Message, SavedHub
from app.models.storage import FileAsset
from app.models.bazaar import BazaarProduct, SavedProduct