---
name: audience-analytics
description: "Measure and understand the audience on TikTok, Instagram Reels, Facebook Reels and YouTube Shorts: which KPIs matter per platform, pulling metrics (APIs + dashboards), reading retention/engagement/shares, audience profile and active hours, weekly report template and turning findings into actions. Use it for reports, 'what worked', audience profile or posting-time questions."
---

# Audience analytics

Tools: `pull_metrics` (snapshot → `analytics/metrics.csv`; YouTube, Instagram and TikTok APIs) and `insights_report`
(per-platform medians, engagement, best weekdays, top/bottom). Facebook and deeper metrics (retention, follows,
audience) come from the dashboards via `agent-browser-upload` → "Reading insights".

## KPIs that matter (in this order)
1. **Retention**: % watched to the end / average watch time vs length; where the curve drops (hook problem = drop in 0-3 s).
2. **Shares and saves per view**: strongest distribution signals on TikTok and Instagram.
3. **Follows per 1,000 views**: content that builds an audience vs one-off views.
4. **Comments per view** and their quality (questions = demand for the next video).
5. **Views**: outcome, not cause. Compare medians, not totals; one viral video skews means.

## Cadence
- Snapshot daily or at least at +2 days and +7 days after each post (`pull_metrics` is append-only, the latest snapshot wins).
- Weekly report every Monday; monthly: audience profile + active hours + review of `post_time`.

## Weekly report template (`analytics/reports/YYYY-Www.md`)
```
# Week YYYY-Www — <accounts>
Data: N videos (tiktok n, instagram n, facebook n, youtube n), snapshot <date>. <confidence note>
## Wins (3)        video · platform · metric vs median · why we think it worked
## Losses (3)      video · platform · metric vs median · likely cause (hook, topic, length, timing)
## Audience        new facts (countries, ages, active hours, comment themes) with source
## Test result     hypothesis · arms · result · keep/drop
## Next week (≤3)  action · owner role · metric that will prove it
```

## Reading rules
- Compare posts of similar age; a 1-day-old post is not "worse" than a 7-day-old one.
- Platform differences are normal (Facebook skews older; YouTube Shorts grows slower but longer).
- Under ~10 videos per platform: report as hints. Never invent numbers; cite the source of each.
