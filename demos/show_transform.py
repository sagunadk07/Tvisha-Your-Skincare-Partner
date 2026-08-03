from torchvision import transforms
from PIL import Image

IMG_PATH = r"C:\Users\sagun\Tvisha Your SkinCare Partner\test-images\1.png"

img = Image.open(IMG_PATH).convert("RGB")
print("STEP 0: raw PIL image")
print(f"  type   = {type(img)}")
print(f"  size   = {img.size}   (width, height)")
print(f"  mode   = {img.mode}")
one_pixel = img.getpixel((0, 0))
print(f"  pixel at (0,0) = {one_pixel}   (R, G, B as 0-255 ints)")
print()

resize = transforms.Resize((224, 224))
resized = resize(img)
print("STEP 1: after Resize((224, 224))")
print(f"  type   = {type(resized)}")
print(f"  size   = {resized.size}")
print(f"  pixel at (0,0) = {resized.getpixel((0, 0))}   (still 0-255 ints)")
print()

to_tensor = transforms.ToTensor()
tensor = to_tensor(resized)
print("STEP 2: after ToTensor()")
print(f"  type   = {type(tensor)}")
print(f"  shape  = {tuple(tensor.shape)}   (channels, height, width)")
print(f"  dtype  = {tensor.dtype}")
print(f"  min/max values = {tensor.min().item():.4f} / {tensor.max().item():.4f}")
print(f"  pixel at [: ,0,0] (R,G,B) = {tensor[:, 0, 0].tolist()}")
print()

normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
normalized = normalize(tensor)
print("STEP 3: after Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])")
print(f"  type   = {type(normalized)}")
print(f"  shape  = {tuple(normalized.shape)}")
print(f"  min/max values = {normalized.min().item():.4f} / {normalized.max().item():.4f}")
print(f"  pixel at [:,0,0] (R,G,B) = {normalized[:, 0, 0].tolist()}")
print()

full_transform = transforms.Compose([resize, to_tensor, normalize])
one_shot = full_transform(img)
print("STEP 4: same result, using transforms.Compose([...]) in one call")
print(f"  shape  = {tuple(one_shot.shape)}")
print(f"  matches manual step-by-step result: {bool((one_shot == normalized).all())}")
print()

batched = one_shot.unsqueeze(0)
print("STEP 5: after .unsqueeze(0), ready for the model")
print(f"  shape  = {tuple(batched.shape)}   (batch, channels, height, width)")
