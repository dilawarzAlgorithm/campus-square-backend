from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database.database import get_db
from app.models import models
from app.core.auth.oauth2 import get_current_user
from app.enum.enum import ResourceType, Semester
from app.schemas.config import AppConfigResponse

router = APIRouter(
    prefix="/api/utils",
    tags=["Utilities"]
)

@router.get("/get-enums")
def get_enums():
    return {"ResourceType": 
            {
                "count": len(ResourceType),
                "values": {item.name: item.value for item in ResourceType}
            },
            "Semester":
            {
                "count": len(Semester),
                "values": {item.name: item.value for item in Semester}
            },
        }

@router.get("/app-campaign", response_model=AppConfigResponse)
def get_app_campaign(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    inst = db.query(models.Institution).filter(models.Institution.id == current_user.institution_id).first()
    
    if not inst:
        return AppConfigResponse(
            version_id="v1", show_popup=False, show_banner=False
        )
        
    return AppConfigResponse(
        version_id=inst.campaign_version_id or "v1",
        show_popup=inst.show_popup or False,
        popup_title=inst.popup_title,
        popup_message=inst.popup_message,
        lottie_url=inst.lottie_url,
        target_route=inst.target_route,
        show_banner=inst.show_banner or False,
        banner_title=inst.banner_title,
        banner_message=inst.banner_message,
        banner_action_url=inst.banner_action_url,
        primary_color_hex=inst.primary_color_hex
    )