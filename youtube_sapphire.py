import os
import re
from datetime import datetime
import pandas as pd
from googleapiclient.discovery import build

# ====== SETTINGS ======
BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "api_key.txt")) as f:
    API_KEY = f.read().strip()

KEYWORDS = ["sapphire"]
TARGET_NEW = 280
SEARCH_QUERIES = [
    "Sapphire Pakistan lawn collection", "Sapphire Pakistan clothing haul",
    "Sapphire Pakistan try on haul", "Sapphire Pakistan eid collection",
    "Sapphire Pakistan sale shopping vlog", "Sapphire online unstitched suits",
    "Sapphire Pakistani brand dresses", "Sapphire winter collection Pakistan",
]
RESULTS_PER_SEARCH = 50
MIN_COMMENTS = 20
COMMENTS_PER_VIDEO = 50
OUTPUT_FILE = os.path.join(BASE, "data", "youtube_comments_sapphire.csv")

STRONG_FASHION = ["lawn", "unstitched", "stitched", "pret", "kurta", "shalwar", "kameez",
                  "embroidered", "fabric", "dress", "dresses", "suit", "suits", "clothing",
                  "clothes", "outfit", "outfits", "fashion", "bridal", "wedding", "festive",
                  "eid", "collection", "shopping"]
BAD_WORDS = ["gpu", "rx", "radeon", "nitro", "graphics", "geforce", "nvidia", "amd", "gaming",
             "cs2", "csgo", "skin", "knife", "galaxy", "samsung", "iphone", "surface",
             "microsoft", "car", "lucid", "sedan", "k-pop", "kpop", "demon", "hunters",
             "ruby", "diamond", "jewel", "jewelry", "jewellery", "ring", "gem", "gemstone",
             "necklace", "minecraft", "roblox", "diy", "tutorial", "cutting", "stitching",
             "pc", "laptop", "phone"]
OTHER_BRANDS = ["khaadi", "khaddi", "gul ahmed", "gulahmed", "junaid", "alkaram", "alkram",
                "limelight", "nishat", "ego", "ethnic", "silk avenue", "sana safinaz",
                "maria b", "bonanza", "breakout", "outfitters", "miniso", "zellbury",
                "beechtree", "charizma", "asim jofa", "agha noor", "makeupcity", "hemani"]

youtube = build("youtube", "v3", developerKey=API_KEY)

# ====== HELPERS ======
def clean_text(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"@\w+", "@user", text)
    return re.sub(r"\s+", " ", text).strip()

def has_word(text, words):
    return any(re.search(r"\b" + re.escape(w) + r"\b", text) for w in words)

def get_category(title):
    t = (title or "").lower()
    if any(w in t for w in ["sale", "off", "discount"]): return "Sale/Discount"
    if any(w in t for w in ["eid", "ramadan", "festive", "wedding", "bridal", "shaadi"]): return "Festive/Wedding"
    if any(w in t for w in ["review", "haul", "unboxing", "try on", "try-on"]): return "Review/Haul"
    if any(w in t for w in ["fashion show", "ramp", "runway"]): return "Fashion Show"
    if any(w in t for w in ["lawn", "collection", "new", "launch", "summer", "winter"]): return "New Collection"
    return "Ad/Campaign/Other"

def is_relevant(inf):
    title = inf["title"].lower()
    title_channel = title + " " + inf["channel"].lower()
    all_text = title_channel + " " + inf["tags"].lower()
    if not any(k in title_channel for k in KEYWORDS): return False
    if not has_word(all_text, STRONG_FASHION): return False
    if has_word(all_text, BAD_WORDS): return False
    if has_word(title, OTHER_BRANDS): return False
    if re.search(r"(^|\s)j\.(\s|,|$)", title): return False
    return True

def search_videos(query, n):
    try:
        res = youtube.search().list(part="id", q=query, type="video", order="relevance",
                                    regionCode="PK", maxResults=n).execute()
        return [i["id"]["videoId"] for i in res.get("items", [])]
    except Exception as e:
        print("   Search error:", str(e)[:100])
        return []

def get_video_infos(video_ids):
    infos = {}
    for i in range(0, len(video_ids), 50):
        res = youtube.videos().list(part="snippet,statistics",
                                    id=",".join(video_ids[i:i + 50])).execute()
        for v in res.get("items", []):
            s = v["statistics"]
            infos[v["id"]] = {
                "title": v["snippet"]["title"], "channel": v["snippet"]["channelTitle"],
                "published": v["snippet"]["publishedAt"],
                "tags": " ".join(v["snippet"].get("tags", [])[:10]),
                "views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)),
                "comments_count": int(s.get("commentCount", 0)),
            }
    return infos

def get_comments(video_id, limit):
    comments, token = [], None
    try:
        while len(comments) < limit:
            res = youtube.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=100, order="relevance",
                textFormat="plainText", pageToken=token).execute()
            for item in res["items"]:
                c = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({"text": clean_text(c["textDisplay"]),
                                 "comment_likes": c["likeCount"]})
            token = res.get("nextPageToken")
            if not token:
                break
    except Exception as e:
        print("   Comments band/error:", str(e)[:60])
    return comments[:limit]

# ====== MAIN ======
old_ids = set()
for fname in ["youtube_comments_raw.csv", "youtube_comments_extra.csv"]:
    p = os.path.join(BASE, "data", fname)
    if os.path.exists(p):
        old_ids |= set(pd.read_csv(p)["video_id"].unique())

today = datetime.now().strftime("%Y-%m-%d")
ids = []
for q in SEARCH_QUERIES:
    ids += search_videos(q, RESULTS_PER_SEARCH)
ids = [v for v in dict.fromkeys(ids) if v not in old_ids]
print("Nayi candidate videos:", len(ids))

infos = get_video_infos(ids)
good = [(v, i) for v, i in infos.items() if is_relevant(i) and i["comments_count"] >= MIN_COMMENTS]
good.sort(key=lambda x: x[1]["comments_count"], reverse=True)
print("Acchi videos:", len(good))

rows = []
for vid, inf in good:
    if len(rows) >= TARGET_NEW:
        break
    cms = get_comments(vid, COMMENTS_PER_VIDEO)
    if len(cms) < MIN_COMMENTS:
        continue
    official = any(k in inf["channel"].lower() for k in KEYWORDS)
    for c in cms:
        rows.append({
            "brand": "Sapphire", "video_id": vid,
            "video_title": clean_text(inf["title"]),
            "channel_title": clean_text(inf["channel"]),
            "source_type": "Brand Official" if official else "Creator/Reviewer",
            "video_category": get_category(inf["title"]),
            "tags": inf["tags"], "published_utc": inf["published"],
            "collection_date": today, "views": inf["views"],
            "likes": inf["likes"], "comments_count": inf["comments_count"],
            "comment_text": c["text"], "comment_likes": c["comment_likes"],
        })
    print(f"Done: {len(cms)} comments | {inf['title'][:80]}")      # ab sirf ek dafa print hoga

rows = rows[:TARGET_NEW]
if not rows:
    print("\nKoi nayi video nahi mili. Upar ka output mujhe bhej do.")
else:
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print("\nNaye comments:", len(df), "| Naye videos:", df["video_id"].nunique())
    print("Saved:", OUTPUT_FILE)