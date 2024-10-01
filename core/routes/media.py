from fastapi import APIRouter, UploadFile, File, HTTPException
import cloudinary
import cloudinary.uploader

media_router = APIRouter(tags=["Media"])

@media_router.post("/upload-image", status_code=201)
async def upload_image(file: UploadFile = File(...)):
    try:
        result = cloudinary.uploader.upload(file.file)
        return {"image_url": result["secure_url"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Image upload failed")



