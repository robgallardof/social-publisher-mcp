---
name: trend-research
description: "Research trends, sounds, formats, hashtags, keywords and competitors for TikTok, Instagram Reels, Facebook Reels and YouTube Shorts, and verify platform rules/API/algorithm claims with sources. Use it for 'what is trending', hashtag/keyword research, competitor teardown, or before trusting any claim about how a platform works."
---

# Trend research

## Sources, best first
1. **Official**: TikTok Creative Center (trends: hashtags, songs, creators, videos by country), TikTok Newsroom,
   Instagram @creators and Meta for Creators, YouTube Creator Insider / YouTube Official Blog / Studio "Inspiration"
   and "Research" tabs, developer docs (developers.tiktok.com, developers.facebook.com, developers.google.com/youtube).
2. **Platform search itself** (browser): search the niche keyword, sort recent, note what format the top 10 share,
   autocomplete suggestions = what people search.
3. **Industry**: Social Media Today, platform-specific newsletters, reputable agencies' studies (state the sample).
4. **Creators in the niche**: 5-10 accounts of similar size and 3 larger ones.

Use the web search tool for 1 and 3; the browser (`agent-browser-upload` tools) for 2 and 4.

## Competitor teardown (per account, last 20 posts)
Posting frequency and time; top 3 by views vs their median; hook shapes; length; caption style; hashtags reused;
series; what the comments ask for. Output the **patterns**, never their content to copy.

## Output (`analytics/research/YYYY-MM-DD-<topic>.md`)
```
## Opportunity: <name>          expires ~<date>
What: …        Evidence: links + dates + numbers
Fit with brand: high/med/low — why
How we use it: existing video <file> / new video idea brief for the editor
Hashtags/keywords: …            Sound availability (business accounts): yes/no/unknown
```

## Verifying claims
Algorithm/limit claims need a source and a date; vendor blogs contradict each other, prefer official docs and say
when unsure. If a limit in `social_forge/domain/platforms.py` is outdated: change it, adjust `tests/test_domain.py`
if needed, run tests and `python scripts/sync.py`.
