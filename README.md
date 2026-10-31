# Pakistani Social Media Content Detective

**What type of social-media content gets Pakistani audiences to engage?**
A sentiment and engagement analysis of YouTube comments on five Pakistani fashion brands.

Big Data Analytics project, BSAI 7th semester, University of Management and Technology (UMT)
Author: Amna (F2023376429, Section A1)

---

## Project overview

Acting as a junior digital-marketing data scientist, this project collects public YouTube comments about five Pakistani fashion/retail brands, measures their sentiment (English, Roman Urdu, Urdu script and mixed), and relates sentiment and content type to engagement.

**Brands:** Khaadi, Gul Ahmed, Sapphire, J. Junaid Jamshed, Alkaram Studio

**Final dataset:** 1,794 comments from 35 YouTube videos (6 brand-official videos and 29 creator/reviewer videos), collected in October 2026 with the YouTube Data API v3. Commenter usernames were never stored.

> Instagram was the first plan, but Instagram blocked the login (security checkpoint) and automated scraping is against its rules. After talking to my teacher, the project moved to YouTube, which has an official API. No Instagram data is used.

## Questions answered

| Goal in the project brief | Where |
|---|---|
| Compare platform / brand performance | Report 7.1, graph g5 |
| Which content types get the most engagement | Report 7.2, graphs g6, g7 |
| Popular topics and hashtags | Report 7.4, graphs g8, g9 |
| Sentiment analysis of comments | Report 5, 6, 7.3, graphs g1 to g4 |
| Sentiment vs engagement | Report 7.5, graph g10 |
| Responsive audience segments and best posting day/time | Report 7.6, 7.7, graph g11 |
| AI-assisted marketing recommendations | Report 8 |

## Key results

- **75%** of all comments are positive, 15% neutral, 10% negative.
- Positive share by brand (song comments excluded): Khaadi 90%, J. Junaid Jamshed 87%, Gul Ahmed 69%, Sapphire 67%, Alkaram Studio 55%. Alkaram has the most negative comments (21%).
- Average engagement rate (likes + comments) / views: creator/reviewer videos 2.41% vs brand-official videos 1.53%. Review/haul (2.78%) and sale (2.30%) videos beat new-collection videos (1.38%).
- 39% of Gul Ahmed's comments, and all 10 of the most-liked comments, are about the soundtrack of its official lawn ads.
- Order/availability comments are the least positive topic (15% positive).
- Sentiment and engagement rate are only weakly related (Spearman 0.39, falling to 0.24 after removing the effect of views). View count is the strongest factor (-0.81).
- The sentiment model was checked on 60 manually labelled comments: **75% accuracy (78% after a small correction rule)**.

These results come from a small sample (35 videos). Treat video-level results as indicative, not conclusive. See the limitations in the report.

## Folder structure

```
social-media-sentiment-analysis/
├── youtube_collector.py        # main data collection (YouTube Data API)
├── youtube_topup.py            # extra Khaadi / Sapphire collection
├── youtube_sapphire.py         # stricter Sapphire collection
├── youtube_analysis.ipynb      # cleaning, language/topic tags, accuracy check, graphs, correlations, segments
├── colab_sentiment.ipynb       # sentiment model (run on Google Colab)
├── data/                       # CSV files (see below)
├── outputs/                    # 11 graphs (g1 to g11 PNG)
├── report/                     # Word report
├── archive/                    # reference files from the course repository and old backups
├── .gitignore                  # keeps api_key.txt out of Git
└── README.md
```

### Data files (`data/`)

| File | Contents |
|---|---|
| `youtube_comments_raw.csv` | First collection (2,000 comments) |
| `youtube_comments_extra.csv` | Top-up run for Khaadi and Sapphire. Only the Khaadi haul/try-on/sale videos were used; its Sapphire rows were unrelated videos (graphics cards, cars, phones) and were discarded |
| `youtube_comments_sapphire.csv` | Stricter Sapphire run (280 comments, one multi-brand video removed afterwards) |
| `youtube_cleaned.csv` | Merged and cleaned data with language and topic tags (1,794 rows) |
| `youtube_sentiment.csv` | Cleaned data plus model sentiment (made in Colab) |
| `youtube_final.csv` | Final data with `sentiment_final` after the correction rule; used for all graphs |
| `youtube_segments.csv` | Final data plus the audience segment of each comment |
| `manual_label_sample.csv` / `manual_label_sample_DONE.csv` | The 60 comments labelled by hand to check the model |

Main columns: `brand`, `video_id`, `video_title`, `channel_title`, `source_type` (Brand Official / Creator/Reviewer), `video_category`, `tags`, `published_utc`, `collection_date`, `views`, `likes`, `comments_count`, `comment_text`, `comment_likes`, `language`, `topic`, `sentiment`, `sentiment_final`, `engagement`, `engagement_rate`.

## Methods in short

1. **Collection:** YouTube Data API v3 searches (Pakistan region) per brand, filtered by brand name, fashion words and unwanted words; top-level comments, up to 60 per video, in YouTube's relevance order.
2. **Cleaning:** removed multi-brand and unrelated videos, duplicates and empty comments; lower-cased text; Pakistan time (UTC+5) for day and hour.
3. **Language and topic:** rule-based Roman Urdu / English detector (about 85% accurate in a small check) and keyword topics (Music/Song, Price/Sale, Order/Availability, Product/Style, Praise/Dua, Other).
4. **Sentiment:** `cardiffnlp/twitter-xlm-roberta-base-sentiment` (multilingual transformer) on Google Colab, then a small rule that fixes misspelt Roman Urdu praise labelled negative (16 comments).
5. **Validation:** 60 comments labelled by hand without seeing the model's answer.
6. **Engagement:** engagement rate = (likes + comment count) / views x 100 per video; Spearman and rank-based partial correlation.
7. **Segments:** KMeans (K = 4, written in NumPy) on language, topic, sentiment, comment length, emojis and likes.

## How to run

1. Install the libraries:
   ```bash
   pip install google-api-python-client pandas numpy matplotlib seaborn
   ```
2. Create a YouTube Data API v3 key in Google Cloud Console and save it in a file called `api_key.txt` next to the scripts. **Never commit this file** (it is listed in `.gitignore`).
3. Collect data: `python youtube_collector.py` (then the top-up scripts if needed). Results change over time, so a new run returns different videos and comments. The quota is limited per day.
4. Open `youtube_analysis.ipynb` in VS Code and read the cells from top to bottom. Each cell has a heading comment that says what it does.
5. Sentiment needs PyTorch, so it runs in `colab_sentiment.ipynb` on Google Colab (upload `youtube_cleaned.csv`, download `youtube_sentiment.csv` into `data/`).

> **Please do not use "Run All" on the notebook.** The cells overwrite files in order. In particular, the cell that creates `manual_label_sample.csv` would erase the hand-made labels. The notebook is a record of the work done.

## Limitations

- Only 35 videos (6 to 8 per brand), fewer than the 60 to 100 posts in the brief; YouTube only.
- Videos from 2017 to 2026; 29 of 35 are creator videos; Khaadi and J. Junaid Jamshed have no official video. Sentiment towards a brand cannot be fully separated from sentiment towards the creator.
- Comments are YouTube's top comments, not a random sample.
- Engagement figures belong to the whole video (n = 35), and view count has a strong effect. Correlations are not proof of cause.
- Sentiment accuracy is 75% to 78% on 60 comments labelled by one person, with no negative comments in that sample. Negative percentages are indicative.
- Language and topic tags are keyword based; only 15 comments are in Urdu script.
- Segments are exploratory (no clear elbow).

## Privacy and ethics

Only public comments were collected through the official API. Commenter names were not stored and @mentions were replaced by "@user". The API key is not part of the repository.

## AI assistance

An AI assistant (Claude, by Anthropic) helped with code, debugging and drafting text, including the marketing recommendations. I collected the data, ran all the code, labelled the 60 validation comments and checked the outputs.

## Reference files

`archive/` holds files that came with the course repository (the example notebook, the example dataset and the original README as `README_teacher.md`) and old backups. They are not used in this analysis.
