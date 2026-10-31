[Social_Media_Sentiment_Analysis.ipynb](https://github.com/user-attachments/files/30217296/Social_Media_Sentiment_Analysis.ipynb)
# Social Media Sentiment & Engagement Analysis

An end-to-end exploratory data analysis (EDA) of 2,260+ social media posts across five platforms, exploring how sentiment, platform, follower size, and timing relate to post engagement.

##  Project Overview

This project analyzes social media post data to understand:
- Which platforms and content types generate the most engagement (likes, shares, comments)
- How sentiment (Positive / Negative / Neutral) varies by platform and country
- Whether follower count or verification status affects engagement
- Time-based patterns in posting volume and engagement (day of week, month)
- Relationships between engagement metrics

##  Files

| File | Description |
|---|---|
| `Social_Media_Sentiment_Analysis.ipynb` | Full Jupyter/Colab notebook — data loading, cleaning, EDA, visualizations, and insights |
| `social_media_sentiment_raw.csv` | Raw, uncleaned dataset (2,260 rows, 13 columns) |

##  Dataset

- **Records:** 2,260 posts (before cleaning)
- **Platforms:** Twitter, Instagram, Facebook, TikTok, LinkedIn
- **Countries:** 12 countries covered
- **Time range:** January 2023 – December 2024
- **Columns:** `post_id`, `timestamp`, `platform`, `user`, `followers_count`, `verified`, `text`, `hashtags`, `country`, `likes`, `retweets_shares`, `comments`, `sentiment`

##  Tools & Libraries

- Python
- Pandas, NumPy — data cleaning and manipulation
- Matplotlib, Seaborn — visualizations
- Google Colab / Jupyter Notebook

##  Data Cleaning Steps

- Removed duplicate rows
- Fixed data types (e.g., `followers_count` stored as text with commas, `timestamp` converted to datetime)
- Standardized inconsistent text casing/whitespace in categorical columns
- Handled missing values with column-appropriate strategies (imputation, fill, or row removal)
- Corrected invalid values (negative likes)
- Created derived features: `total_engagement`, `engagement_rate`, `day_of_week`, `hour`, `hashtag_count`, `follower_tier`

##  Visualizations Included

Pie chart, bar plots, stacked bar, histograms, box plot, scatter plot, correlation heatmap, line chart (monthly trend), grouped bar chart, horizontal bar chart, and a second heatmap (platform × day of week) — 12 visualizations in total.

##  Key Insights

1. **TikTok drives the highest engagement per post**, while LinkedIn shows the lowest — consistent with each platform's content style and audience.
2. **Positive sentiment correlates with higher engagement**, but negative posts aren't far behind, suggesting emotional intensity (not just positivity) drives interaction.
3. **Engagement metrics move together** — likes, shares, and comments are strongly correlated.
4. **Verified accounts get a higher engagement rate** per 1,000 followers than unverified accounts of similar size.
5. **Posting activity and engagement show mild weekly patterns**, slightly higher midweek than on weekends.

##  How to Run

1. Clone this repository or download the files.
2. Open `Social_Media_Sentiment_Analysis.ipynb` in [Google Colab](https://colab.research.google.com) or Jupyter Notebook.
3. Upload `social_media_sentiment_raw.csv` when prompted (or place it in the same directory / your mounted Google Drive).
4. Run all cells in order.

##  Author

Mrudula KP
