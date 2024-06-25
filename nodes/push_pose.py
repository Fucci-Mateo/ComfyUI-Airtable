from PIL import Image
import requests
import os
import numpy as np
import requests
import cloudinary
import cloudinary.uploader
import random
import json

# enviorment variables
env=json.load(open("{}/env.json".format(os.getcwd())))
CREDENTIALS=env['CREDENTIALS']
CONFIG=env['CONFIG']




img_id=str(random.randint(0, 10000))
TEMPORAL_SKELETON_PATH = CONFIG["temporalPath"] + "temporalSkeleton-{}".format(img_id) + ".png"
TEMPORAL_POSE_PATH = CONFIG["temporalPath"] + "temporalPose-{}".format(img_id) + ".png"


# Configuration  
cloudinary.config( 
    cloud_name = CREDENTIALS["CLOUDINARY_CLOUD_NAME"], 
    api_key =  CREDENTIALS["CLOUDINARY_API_KEY"], 
    api_secret = CREDENTIALS["CLOUD_ORDINARY_SECRET"], # Click 'View Credentials' below to copy your API secret
    secure=True
)


def tensor2pil(image):
    image = image.squeeze()  # Remove any singleton dimensions
    if image.dim() == 3 and image.shape[0] in [1, 3]:  # (C, H, W) or (H, W, C)
        if image.shape[0] == 1:  # Grayscale
            image = image.repeat(3, 1, 1)  # Convert to RGB
        image = image.permute(1, 2, 0)  # Convert to (H, W, C)
    return Image.fromarray(np.clip(255. * image.cpu().numpy(), 0, 255).astype(np.uint8))

def save_image(image, file_path):
    image = tensor2pil(image)  # Convert tensor to PIL image
    image.save(file_path, format='PNG')
    return ()
     
def upload_image_cloudinary(image_path,public_id):
    upload_result = cloudinary.uploader.upload(image_path , public_id=public_id)
    print(upload_result["secure_url"])
    return upload_result["secure_url"]

def delete_image_cloudordinary(public_id):
    result=cloudinary.uploader.destroy(public_id)
    print(result)


def pushPose(pose_name,pose_image_url,pose_skeleton_url):
    url = "https://api.airtable.com/v0/{}/{}".format(CREDENTIALS["AIRTABLE_BASE_ID"], CREDENTIALS['AIRTABLE_POSES_TABLE'])

    headers = {
        "Authorization": "Bearer {}".format(CREDENTIALS["AIRTABLE_TOKEN"]),
        "Content-Type": "application/json"
    }
    data = {
        "fields": {
            "name": pose_name,
            "image": [
                {
                    "url": pose_image_url }
            ],
            "skeleton": [
                {
                    "url": pose_skeleton_url
                    }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return "Success"
    else:
        return "Failed"


    
class PushPoseToAirtable:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "poseName": ("STRING", {"singleline": True, "dynamicPrompts": False}),
                "poseImage": ("IMAGE",),
                "skeletonImage": ("IMAGE",)

            }
        }


    RETURN_TYPES = ("STRING",)
    FUNCTION = "push"
    CATEGORY = "image"





    def push(self,poseName, poseImage, skeletonImage):
        #create ids to push to cloudinary
        pose_id= 'pose-{}'.format(img_id)
        skeleton_id= 'skeleton-{}'.format(img_id)

        #save images locally
        save_image(poseImage,TEMPORAL_POSE_PATH)
        save_image(skeletonImage,TEMPORAL_SKELETON_PATH)

        #upload images to cloudinary
        pose_cloud_url=upload_image_cloudinary(TEMPORAL_POSE_PATH,pose_id)
        skeleton_cloud_url=upload_image_cloudinary(TEMPORAL_SKELETON_PATH,skeleton_id)

        #push to airtable
        result=pushPose(poseName,pose_cloud_url,skeleton_cloud_url)

        #delete images from cloudinary
        delete_image_cloudordinary(pose_id)
        delete_image_cloudordinary(skeleton_id)

        #delete images from local
        os.remove(TEMPORAL_POSE_PATH)
        os.remove(TEMPORAL_SKELETON_PATH)
        
        print(os.getcwd())
        return (result)
    
