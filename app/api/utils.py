from fastapi import APIRouter
from app.enum.enum import ResourceType, Semester

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
