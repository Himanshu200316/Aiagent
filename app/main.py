from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse

from .config import settings
from .models import CredentialsIn, AdRequest, ScheduleRequest, CerebrusMessage, GeneratedAd
from .storage import Storage
from .scheduler import PostScheduler
from .generation.caption_generator import generate_caption
from .generation.image_generator import generate_image
from .utils.prompt_utils import build_prompt_key
from .conversation import ConversationManager

app = FastAPI(title=settings.app_name)
storage = Storage()
scheduler = PostScheduler(storage)
conv = ConversationManager(storage, scheduler)


@app.on_event("startup")
def schedule_existing_users():
    for user_id in storage.list_users():
        try:
            scheduler.schedule_user(user_id)
        except Exception:
            # continue scheduling others even if one fails
            pass


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/credentials/{platform}")
def save_credentials(platform: str, user_id: str = Form(...), payload: UploadFile | None = None):
    # Accept JSON payload via file upload or simple form fields
    import json
    if payload is not None:
        data = json.loads(payload.file.read().decode())
    else:
        return JSONResponse(status_code=400, content={"error": "missing_payload"})
    storage.save_credentials(user_id, platform, data)
    return {"status": "saved"}


@app.post("/ad/request", response_model=GeneratedAd)
def ad_request(req: AdRequest):
    if req.use_uploaded_image:
        img_path = storage.get_uploaded_image_path(req.user_id, req.use_uploaded_image)
        if not img_path:
            return JSONResponse(status_code=400, content={"error": "image_not_found"})
        result = scheduler.generate_and_post(
            req.user_id,
            req.product_description,
            req.tone,
            req.target_audience,
            req.platforms,
            instagram_post_type=req.instagram_post_type,
            use_uploaded_image_path=img_path,
        )
    else:
        result = scheduler.generate_and_post(
            req.user_id,
            req.product_description,
            req.tone,
            req.target_audience,
            req.platforms,
            instagram_post_type=req.instagram_post_type,
        )
    return GeneratedAd(caption=result["caption"], image_path=result["image_path"], prompt_key=result["prompt_key"])


@app.post("/upload-image")
def upload_image(user_id: str = Form(...), file: UploadFile = File(...)):
    contents = file.file.read()
    path = storage.save_image(user_id, contents, suffix=".png")
    image_id = path.split("/")[-1]
    return {"image_id": image_id, "path": path}


@app.post("/schedule")
def set_schedule(req: ScheduleRequest):
    storage.save_schedule(req.user_id, req.hour, req.minute, req.timezone)
    scheduler.schedule_user(req.user_id)
    return {"status": "scheduled"}


@app.get("/history")
def history(user_id: str):
    return {"history": storage.list_history(user_id)}


@app.post("/post/now")
def post_now(req: AdRequest):
    result = scheduler.generate_and_post(
        req.user_id,
        req.product_description,
        req.tone,
        req.target_audience,
        req.platforms,
        instagram_post_type=req.instagram_post_type,
    )
    return result


@app.post("/webhook/cerebrus")
def cerebrus_webhook(msg: CerebrusMessage):
    reply = conv.handle(msg.user_id, msg.message, msg.payload)
    return reply
