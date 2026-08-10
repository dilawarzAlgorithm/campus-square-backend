from typing import Optional
from pydantic import BaseModel

class AppConfigResponse(BaseModel):
    version_id: str
    show_popup: bool
    popup_title: Optional[str] = None
    popup_message: Optional[str] = None
    lottie_url: Optional[str] = None
    target_route: Optional[str] = None
    
    show_banner: bool
    banner_title: Optional[str] = None
    banner_message: Optional[str] = None
    banner_action_url: Optional[str] = None
    
    primary_color_hex: Optional[str] = None

class AppConfigUpdate(BaseModel):
    version_id: Optional[str] = None
    show_popup: Optional[bool] = None
    popup_title: Optional[str] = None
    popup_message: Optional[str] = None
    lottie_url: Optional[str] = None
    target_route: Optional[str] = None
    
    show_banner: Optional[bool] = None
    banner_title: Optional[str] = None
    banner_message: Optional[str] = None
    banner_action_url: Optional[str] = None
    
    primary_color_hex: Optional[str] = None