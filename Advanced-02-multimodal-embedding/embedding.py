import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

# 1️⃣ 모델 로드 (이미지-텍스트 공유 임베딩 모델)
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# 2️⃣ 입력 준비
text = ["a photo of a cat"]
image = Image.open("cat.jpeg")

inputs = processor(
    text=text,
    images=image,
    return_tensors="pt",
    padding=True
)

# 3️⃣ 임베딩 추출
with torch.no_grad():
    outputs = model(**inputs)

text_embeds = outputs.text_embeds      # 텍스트 벡터
image_embeds = outputs.image_embeds    # 이미지 벡터

# 4️⃣ 정규화 (유사도 계산을 위해 보통 수행)
text_embeds = text_embeds / text_embeds.norm(dim=-1, keepdim=True)
image_embeds = image_embeds / image_embeds.norm(dim=-1, keepdim=True)

print("Text embedding shape:", text_embeds.shape)
print("Image embedding shape:", image_embeds.shape)

# 5️⃣ 텍스트-이미지 유사도 계산
similarity = (text_embeds @ image_embeds.T).item()
print("Similarity score:", similarity)