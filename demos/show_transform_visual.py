import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from torchvision import transforms
from PIL import Image

IMG_PATH = r"C:\Users\sagun\Tvisha Your SkinCare Partner\test-images\1.png"
OUT_PATH = r"C:\Users\sagun\Tvisha Your SkinCare Partner\demos\transform_steps.png"

img = Image.open(IMG_PATH).convert("RGB")

resize = transforms.Resize((224, 224))
resized = resize(img)

to_tensor = transforms.ToTensor()
tensor = to_tensor(resized)  # (3,224,224), 0-1

normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
normalized = normalize(tensor)  # (3,224,224), roughly -2 to 2.6

# For display: matplotlib wants (H, W, C)
tensor_disp = tensor.permute(1, 2, 0).numpy()  # 0-1, displays normally

# Raw normalized values shown AS-IS: imshow clips to [0,1], so negatives clip to 0
normalized_raw_disp = normalized.permute(1, 2, 0).numpy()
normalized_raw_clipped = np.clip(normalized_raw_disp, 0, 1)

# Same normalized data, but min-max rescaled back to 0-1 just so we can SEE the content
norm_min, norm_max = normalized_raw_disp.min(), normalized_raw_disp.max()
normalized_rescaled = (normalized_raw_disp - norm_min) / (norm_max - norm_min)

fig, axes = plt.subplots(1, 4, figsize=(16, 4.5))

axes[0].imshow(img)
axes[0].set_title(f"0. Original\n{img.size[0]}x{img.size[1]} px, 0-255 ints")

axes[1].imshow(resized)
axes[1].set_title("1. After Resize\n224x224 px, 0-255 ints")

axes[2].imshow(tensor_disp)
axes[2].set_title("2. After ToTensor()\n224x224, values 0.0-1.0\n(looks identical)")

axes[3].imshow(normalized_raw_clipped)
axes[3].set_title("3. After Normalize()\nshown AS-IS (clipped to 0-1)\nlooks broken/washed out")

for ax in axes:
    ax.axis("off")

plt.tight_layout()
plt.savefig(OUT_PATH, dpi=120)
print(f"Saved: {OUT_PATH}")

# second figure: proving the normalized data still holds the same picture,
# just shifted in number range -- rescale it back for viewing
fig2, axes2 = plt.subplots(1, 3, figsize=(12, 4.5))
axes2[0].imshow(resized)
axes2[0].set_title("Resized (0-255 view)")
axes2[1].imshow(normalized_raw_clipped)
axes2[1].set_title("Normalized, shown raw\n(clipped -> looks wrong)")
axes2[2].imshow(normalized_rescaled)
axes2[2].set_title("Normalized, min-max rescaled\nfor viewing (same content!)")
for ax in axes2:
    ax.axis("off")
plt.tight_layout()
OUT_PATH2 = OUT_PATH.replace(".png", "_rescaled.png")
plt.savefig(OUT_PATH2, dpi=120)
print(f"Saved: {OUT_PATH2}")
