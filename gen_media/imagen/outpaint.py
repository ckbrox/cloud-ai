from google.genai import Client, types
import google.auth
from google.genai.types import RawReferenceImage, MaskReferenceImage, MaskReferenceConfig, EditImageConfig, Image

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")



raw_ref = RawReferenceImage(reference_image=Image.from_file(location='josh.png'), reference_id=0)

mask_ref = MaskReferenceImage(
    reference_id=1,
    reference_image=Image.from_file(location='josh_mask.png'),
    config=MaskReferenceConfig(
        mask_mode="MASK_MODE_USER_PROVIDED",
        mask_dilation=0.03,
    ),
)

image = client.models.edit_image(
    model="imagen-3.0-capability-001",
    prompt="A man standing in a garden in front of a flower wall",
    reference_images=[raw_ref, mask_ref],
    config=EditImageConfig(
        edit_mode="EDIT_MODE_OUTPAINT",
    ),
)

image.generated_images[0].image.save('outpainting2.png')

print(f"Created output image using {len(image.generated_images[0].image.image_bytes)} bytes")
# Example response:
# Created output image using 1234567 bytes