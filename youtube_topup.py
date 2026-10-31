import os
import re
from datetime import datetime
import pandas as pd
from googleapiclient.discovery import build

# ====== SETTINGS ======
BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "api_key.txt")) as f:
    API_KEY = f.read().strip()

BRANDS = {"Khaadi": ["khaadi", "khaddi"], "Sapphire": ["sapphire"]}
TARGET_NEW = {"Khaadi": 160, "Sapphire": 280}     # kitne naye comments chahiye
SEARCH_TEMPLATES = ["{} try on haul", "{} unboxing", "{} eid collection",
                    "{} lawn collection", "{} winter collection",
                    "{} sale shopping vlog", "{} review"]
RESULTS_PER_SEARCH = 50
MIN_COMMENTS = 20
COMMENTS_PER_VIDEO = 40
RAW_FILE = os.path.join(BASE, "data", "youtube_comments_raw.csv")
OUTPUT_FILE = os.path.join(BASE, "data", "youtube_comments_extra.csv")

OTHER_BRANDS = ["khaadi", "khaddi", "gul ahmed", "gulahmed", "sapphire", "junaid",
                "alkaram", "alkram", "limelight", "nishat", "ego", "ethnic",
                "silk avenue", "sana safinaz", "maria b", "bonanza", "breakout",
                "outfitters", "miniso", "zellbury", "beechtree", "charizma",
                "asim jofa", "agha noor", "makeupcity", "hemani"]
FASHION_WORDS = ["lawn", "unstitched", "stitched", "pret", "dress", "suit", "collection",
                 "fashion", "eid", "bridal", "wedding", "festive", "shopping", "haul",
                 "sale", "fabric", "kurta", "shalwar", "winter", "formal", "embroidered",
                 "try on", "try-on", "unboxing", "review", "lookbook", "look book"]
BAD_WORDS = ["k-pop", "kpop", "demon", "ruby", "diamond", "jewel", "jewelry", "ring",
             "gem", "gemstone", "minecraft", "roblox", "car", "engine", "phone", "song",
             "naat", "hadees", "quran", "recipe", "cutting", "stitching", "tutorial", "diy"]

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

def is_relevant(inf, keywords):
    title = inf["title"].lower()
    title_channel = title + " " + inf["channel"].lower()
    all_text = title_channel + " " + inf["tags"].lower()
    if not any(k in title_channel for k in keywords): return False
    if not any(w in all_text for w in FASHION_WORDS): return False
    if has_word(all_text, BAD_WORDS): return False
    others = [w for w in OTHER_BRANDS if w not in keywords]
    if has_word(title, others): return False                       # dusra brand title mein
    if re.search(r"(^|\s)j\.(\s|,|$)", title): return False         # "J." multi-brand
    return True

def search_videos(query, n):
    try:
        res = youtube.search().list(part="id", q=query, type="video",
                                    order="relevance", regionCode="PK",
                                    maxResults=n).execute()
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
                "title": v["snippet"]["title"],
                "channel": v["snippet"]["channelTitle"],
                "published": v["snippet"]["publishedAt"],
                "tags": " ".join(v["snippet"].get("tags", [])[:10]),
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments_count": int(s.get("commentCount", 0)),
            }
    return infos

def get_comments(video_id, limit):
    comments, token = [], None
    try:
        while len(comments) < limit:
            res = youtube.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=100,
                order="relevance", textFormat="plainText", pageToken=token).execute()
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
old_ids = set(pd.read_csv(RAW_FILE)["video_id"].unique())   # purani videos dobara nahi leni
today = datetime.now().strftime("%Y-%m-%d")
rows = []

for brand, keywords in BRANDS.items():
    print(f"\n--- {brand} (target: {TARGET_NEW[brand]} naye comments) ---")
    ids = []
    for tpl in SEARCH_TEMPLATES:
        ids += search_videos(tpl.format(brand), RESULTS_PER_SEARCH)
    ids = [v for v in dict.fromkeys(ids) if v not in old_ids]
    print(f"   Nayi candidate videos: {len(ids)}")

    infos = get_video_infos(ids)
    good = [(v, i) for v, i in infos.items()
            if is_relevant(i, keywords) and i["comments_count"] >= MIN_COMMENTS]
    good.sort(key=lambda x: x[1]["comments_count"], reverse=True)
    print(f"   Acchi videos: {len(good)}")

    brand_rows = []
    for vid, inf in good:
        if len(brand_rows) >= TARGET_NEW[brand]:
            break
        cms = get_comments(vid, COMMENTS_PER_VIDEO)
        if len(cms) < MIN_COMMENTS:
            continue
        official = any(k in inf["channel"].lower() for k in keywords)
        for c in cms:
            brand_rows.append({
                "brand": brand, "video_id": vid,
                "video_title": clean_text(inf["title"]),
                "channel_title": clean_text(inf["channel"]),
                "source_type": "Brand Official" if official else "Creator/Reviewer",
                "video_category": get_category(inf["title"]),
                "tags": inf["tags"], "published_utc": inf["published"],
                "collection_date": today, "views": inf["views"],
                "likes": inf["likes"], "comments_count": inf["comments_count"],
                "comment_text": c["text"], "comment_likes": c["comment_likes"],
            })
        print(f"   Done: {len(cms)} comments | {inf['title'][:70]}")
    rows += brand_rows[:TARGET_NEW[brand]]

# ====== SAVE ======
if not rows:
    print("\nKoi nayi video nahi mili. Upar ka output mujhe bhej do.")
else:
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print("\nNaye comments:", len(df), "| Naye videos:", df["video_id"].nunique())
    print(df.groupby("brand").size())
    print("Saved:", OUTPUT_FILE)