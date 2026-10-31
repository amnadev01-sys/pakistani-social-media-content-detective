import os
import re
from datetime import datetime
import pandas as pd
from googleapiclient.discovery import build

# ====== SETTINGS ======
BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "api_key.txt")) as f:
    API_KEY = f.read().strip()

# brand name : us ke naam ke keywords (title/tags mein check honge)
BRANDS = {
    "Khaadi": ["khaadi", "khaddi"],
    "Gul Ahmed": ["gul ahmed", "gulahmed"],
    "Sapphire": ["sapphire"],
    "J. Junaid Jamshed": ["junaid jamshed", "j. junaid", "j.junaid", "j. lawn"],
    "Alkaram Studio": ["alkaram", "al karam"],
}
SEARCH_TEMPLATES = ["{} lawn collection", "{} review", "{} haul",
                    "{} fashion show", "{} sale"]
RESULTS_PER_SEARCH = 50     # har search se itni videos
MIN_COMMENTS = 20           # is se kam comments wali video skip
COMMENTS_PER_VIDEO = 60     # ek video se max itne comments
BRAND_TARGET = 400          # har brand ke itne comments (5 x 400 = 2000)
OUTPUT_FILE = os.path.join(BASE, "data", "youtube_comments_raw.csv")

youtube = build("youtube", "v3", developerKey=API_KEY)

# ====== HELPERS ======
FASHION_WORDS = ["lawn", "unstitched", "stitched", "pret", "dress", "suit",
                 "collection", "fashion", "eid", "bridal", "wedding", "festive",
                 "shopping", "haul", "sale", "fabric", "kurta", "shalwar",
                 "winter", "ramp", "runway", "formal", "embroidered"]

BAD_PATTERN = r"\b(car|cars|ford|cosworth|engine|phone|iphone|samsung|song|naat|hadees|hadith|quran|allah|bayan|islamic|nasheed|sermon|recipe|cooking|chef|business idea)\b"

def is_relevant(inf, keywords):
    title_channel = (inf["title"] + " " + inf["channel"]).lower()
    all_text = title_channel + " " + inf["tags"].lower()
    has_brand = any(k in title_channel for k in keywords)   # brand ka naam title ya channel mein ho
    has_fashion = any(w in all_text for w in FASHION_WORDS)
    has_bad = re.search(BAD_PATTERN, all_text) is not None
    return has_brand and has_fashion and not has_bad

def clean_text(text):
    text = re.sub(r"<[^>]+>", " ", text or "")   # html tags hatao
    text = re.sub(r"@\w+", "@user", text)        # usernames hatao (privacy)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_category(title):
    t = (title or "").lower()
    if any(w in t for w in ["sale", "off", "discount"]): return "Sale/Discount"
    if any(w in t for w in ["eid", "ramadan", "festive", "wedding", "bridal", "shaadi"]): return "Festive/Wedding"
    if any(w in t for w in ["review", "haul", "unboxing", "try on"]): return "Review/Haul"
    if any(w in t for w in ["fashion show", "ramp", "runway"]): return "Fashion Show"
    if any(w in t for w in ["lawn", "collection", "new", "launch", "summer", "winter"]): return "New Collection"
    return "Ad/Campaign/Other"

def search_videos(query, n):
    try:
        res = youtube.search().list(part="id", q=query, type="video",
                                    order="viewCount", regionCode="PK",
                                    maxResults=n).execute()
        return [i["id"]["videoId"] for i in res.get("items", [])]
    except Exception as e:
        print("   Search error:", str(e)[:100])
        return []

def get_video_infos(video_ids):
    infos = {}
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        res = youtube.videos().list(part="snippet,statistics",
                                    id=",".join(chunk)).execute()
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
                order="relevance", textFormat="plainText",
                pageToken=token).execute()
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
rows = []
today = datetime.now().strftime("%Y-%m-%d")

for brand, keywords in BRANDS.items():
    print(f"\n--- {brand} ---")

    # 1) candidate videos dhoondo
    ids = []
    for tpl in SEARCH_TEMPLATES:
        ids += search_videos(tpl.format(brand), RESULTS_PER_SEARCH)
    ids = list(dict.fromkeys(ids))          # duplicate hatao
    print(f"   Candidate videos: {len(ids)}")

    # 2) filter: brand ka naam ho + comments kaafi hon
    infos = get_video_infos(ids)
    good = []
    for vid, inf in infos.items():
        if is_relevant(inf, keywords) and inf["comments_count"] >= MIN_COMMENTS:
            good.append((vid, inf))
    good.sort(key=lambda x: x[1]["comments_count"], reverse=True)
    print(f"   Acchi videos (brand + {MIN_COMMENTS}+ comments): {len(good)}")

    # 3) comments collect karo
    brand_rows = []
    for vid, inf in good:
        if len(brand_rows) >= BRAND_TARGET:
            break
        cms = get_comments(vid, COMMENTS_PER_VIDEO)
        if len(cms) < MIN_COMMENTS:
            continue
        official = any(k in inf["channel"].lower() for k in keywords)
        for c in cms:
            brand_rows.append({
                "brand": brand,
                "video_id": vid,
                "video_title": clean_text(inf["title"]),
                "channel_title": clean_text(inf["channel"]),
                "source_type": "Brand Official" if official else "Creator/Reviewer",
                "video_category": get_category(inf["title"]),
                "tags": inf["tags"],
                "published_utc": inf["published"],
                "collection_date": today,
                "views": inf["views"],
                "likes": inf["likes"],
                "comments_count": inf["comments_count"],
                "comment_text": c["text"],
                "comment_likes": c["comment_likes"],
            })
            print(f"   Done: {vid} -> {len(cms)} comments | {inf['title'][:50]}")

    rows += brand_rows[:BRAND_TARGET]
    print(f"   {brand} total: {min(len(brand_rows), BRAND_TARGET)} comments")

# ====== SAVE ======
if not rows:
    print("\nKoi data nahi mila. Upar ka output mujhe bhej do.")
else:
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print("\nTotal comments:", len(df), "| Videos:", df["video_id"].nunique())
    print(df.groupby("brand").size())
    print("Saved:", OUTPUT_FILE)