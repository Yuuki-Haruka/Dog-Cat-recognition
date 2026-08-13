import os
import zipfile
import requests
import time
import random
from PIL import Image
import io

BASE_DIR = "cat_dog"
TRAIN_CAT_DIR = os.path.join(BASE_DIR, "train", "cats")
TRAIN_DOG_DIR = os.path.join(BASE_DIR, "train", "dogs")
TEST_DIR = os.path.join(BASE_DIR, "test")

for d in [TRAIN_CAT_DIR, TRAIN_DOG_DIR, TEST_DIR]:
    os.makedirs(d, exist_ok=True)

ZIP_NAME = "cat_dog.zip"
MIN_SIZE = 150
MAX_ASPECT = 2.0

def is_clean_image(content):
    try:
        img = Image.open(io.BytesIO(content)).convert("RGB")
        w, h = img.size
        if w < MIN_SIZE or h < MIN_SIZE:
            return False
        ratio = max(w, h) / min(w, h)
        if ratio > MAX_ASPECT:
            return False
        return True
    except Exception:
        return False

def save_image(content, path):
    try:
        img = Image.open(io.BytesIO(content)).convert("RGB")
        img.save(path, "JPEG", quality=95)
        return True
    except Exception as e:
        print(f"Save failed: {e}")
        return False

DOG_BREED = "retriever/golden"
def fetch_dog_url():
    try:
        r = requests.get(
            f"https://dog.ceo/api/breed/{DOG_BREED}/images/random",
            timeout=10
        )
        if r.status_code == 200:
            return r.json().get("message")
    except Exception:
        pass
    return None

def download_dogs(folder, target, label):
    count = 0
    attempts = 0
    while count < target:
        attempts += 1
        url = fetch_dog_url()
        if not url:
            time.sleep(1)
            continue

        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200 or "image" not in r.headers.get("Content-Type", ""):
                continue
            content = r.content
        except Exception:
            continue

        if not is_clean_image(content):
            print(f"  [{label}] Skipped (bad size/aspect) — attempt {attempts}")
            continue

        filename = f"dog_{count + 1:04d}.jpg"
        if save_image(content, os.path.join(folder, filename)):
            count += 1
            print(f"  [{label}] Dog {count}/{target}")

        time.sleep(0.1)

CAT_API_KEY = ""
CAT_BREED_IDS = ["mcoo", "bsho", "norw", "sibe", "rblu"]

def fetch_cat_url(breed):
    params = {"breed_ids": breed, "limit": 10, "mime_types": "jpg,png"}
    headers = {"x-api-key": CAT_API_KEY} if CAT_API_KEY else {}
    try:
        r = requests.get(
            "https://api.thecatapi.com/v1/images/search",
            params=params, headers=headers, timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            return [item.get("url") for item in data if item.get("url")]
    except Exception:
        pass
    return []

def download_cats(folder, target, label):
    count = 0
    seen_urls = set()

    all_urls = []
    print(f"  Fetching URL pool from {len(CAT_BREED_IDS)} breeds...")
    for breed in CAT_BREED_IDS:
        for _ in range(20):   # 20 requests × 10 results × 5 breeds = up to 1000 URLs
            urls = fetch_cat_url(breed)
            for u in urls:
                if u not in seen_urls:
                    seen_urls.add(u)
                    all_urls.append(u)
            time.sleep(0.1)
    
    random.shuffle(all_urls)
    print(f"  Pool ready: {len(all_urls)} unique URLs")

    for url in all_urls:
        if count >= target:
            break

        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200 or "image" not in r.headers.get("Content-Type", ""):
                continue
            content = r.content
        except Exception:
            continue

        if not is_clean_image(content):
            continue

        filename = f"cat_{count + 1:04d}.jpg"
        if save_image(content, os.path.join(folder, filename)):
            count += 1
            print(f"  [{label}] Cat {count}/{target}")

        time.sleep(0.05)

    if count < target:
        print(f"  WARNING: Only got {count}/{target} cats. Pool exhausted.")

print("=" * 55)
print("Building cat_dog dataset")
print("=" * 55)

print("\n[1/4] Downloading TRAIN dogs (150) — Golden Retriever …")
download_dogs(TRAIN_DOG_DIR, 150, "train/dogs")

print("\n[2/4] Downloading TRAIN cats (150) — fluffy breeds …")
download_cats(TRAIN_CAT_DIR, 150, "train/cats")

print("\n[3/4] Downloading TEST dogs (50) — Golden Retriever …")
download_dogs(TEST_DIR, 50, "test/dogs")

print("\n[4/4] Downloading TEST cats (50) — fluffy breeds …")
download_cats(TEST_DIR, 50, "test/cats")

print("\nCreating ZIP …")
with zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, os.path.dirname(BASE_DIR))
            zipf.write(file_path, arcname)

print("\n" + "=" * 55)
print("Done!")
print(f"ZIP created : {ZIP_NAME}")
print("\nFolder layout:")
for root, dirs, files in os.walk(BASE_DIR):
    depth = root.replace(BASE_DIR, "").count(os.sep)
    indent = "  " * depth
    print(f"{indent}{os.path.basename(root)}/  ({len(files)} files)")
print("=" * 55)