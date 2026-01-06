# Kaggle News Articles Political Bias Classification - Comprehensive Analysis

## Overview

This analysis package provides an in-depth examination of the **Kaggle News Articles For Political Bias Classification** dataset, with comprehensive visualizations and insights focusing on:

- **Geographic Distribution** of news outlets (USA, UK, Qatar, etc.)
- **Political Bias Patterns** (left, leaning-left, center, leaning-right, right)
- **Topic Coverage** by news outlets and countries
- **Temporal Trends** from 2014 to 2025
- **Outlet Characteristics** and their bias profiles

## Dataset Summary

| Metric | Value |
|--------|-------|
| **Total Articles** | 10,832 |
| **Date Range** | 2014-01-04 to 2025-07-10 |
| **Years Covered** | 12 years |
| **Unique News Outlets** | 297 |
| **Countries Represented** | 6 (USA, UK, Qatar, Europe, Canada, Ireland) |
| **Unique Topics** | 65 |
| **Bias Categories** | 5 (left, leaning-left, center, leaning-right, right) |

### Python Analysis Scripts

1. **`analyze_news_bias_dataset.py`** (Main Analysis)
   - Comprehensive dataset loading and processing
   - Geographic mapping of news outlets to countries
   - Generates 12 diverse visualizations
   - Creates detailed outlet summary statistics
   - Exports data to CSV format

### Visualizations

1. **`news_bias_analysis_comprehensive.png`** (12 Plots)
**12-plot comprehensive dashboard covering:**
   1. News articles distribution by geographic location
   2. Top 20 news outlets by article count
   3. Overall bias distribution (pie chart)
   4. Top 15 news topics covered
   5. Bias distribution by country (stacked bar)
   6. Topic-bias relationship heatmap
   7. Article count trends over time (monthly trend lines)
   8. Articles distribution by year
   9. Bias trends by year (percentage)
   10. Top 15 outlets bias distribution
   11. Top 10 topics distribution by bias type
   12. Seasonal patterns (articles by month)

### Data Exports

1. **`news_outlets_summary.csv`**
- Comprehensive outlet information
- Columns: Country, Outlet, Bias Distribution, Unique Topics, First Article, Last Article, Total Articles

## Key Insights

### Geographic Distribution

```
USA:       9,688 articles (89.44%)
UK:        1,030 articles (9.51%)
Qatar:        81 articles (0.75%)
Europe:       22 articles (0.20%)
Canada:       10 articles (0.09%)
Ireland:       1 article (0.01%)
```

### Bias Distribution (Overall)

| Bias Type | Count | Percentage |
|-----------|-------|------------|
| Right | 2,986 | 27.57% |
| Leaning-Left | 2,951 | 27.24% |
| Left | 1,930 | 17.82% |
| Leaning-Right | 1,487 | 13.73% |
| Center | 1,478 | 13.64% |

### Bias Distribution by Country

**USA (9,688 articles)**
- Leaning-Left: 29.59%
- Right: 29.50%
- Left: 16.95%
- Leaning-Right: 15.35%
- Center: 8.61%

**UK (1,030 articles)**
- Center: 59.51%
- Left: 27.96%
- Right: 12.43%
- Leaning-Left: 0.10%

**Qatar (81 articles)**
- Leaning-Left: 100.00%

### Major News Outlets & Their Bias Profile

#### Right-Leaning (USA)
- **Fox News Digital**: 1,707 articles - Consistently RIGHT bias
- **Washington Examiner**: 939 articles - LEANING-RIGHT bias
- Topics: Politics, Elections, World

#### Left/Leaning-Left (USA)
- **CNN Digital**: 901 articles - LEANING-LEFT bias
- **NBC News Digital**: 400 articles - LEANING-LEFT bias
- **Associated Press**: 571 articles - LEFT bias
- Topics: Politics, Elections, World

#### Center/Balanced (UK)
- **BBC News**: 609 articles - CENTER bias
- **Reuters**: 3 articles - CENTER bias
- **Euronews**: 22 articles - CENTER bias

#### Left-Leaning International
- **The Guardian**: 288 articles (UK) - LEFT bias
- **Al Jazeera**: 81 articles (Qatar) - LEANING-LEFT bias

### Top News Topics

**USA Coverage**
1. Politics (1,483 articles - 15.31%)
2. Elections (856 articles - 8.84%)
3. World News (542 articles - 5.59%)
4. Economy & Jobs (537 articles - 5.54%)
5. Middle-East (399 articles - 4.12%)

**UK Coverage**
1. World News (148 articles - 14.37%)
2. Politics (107 articles - 10.39%)
3. Middle-East (72 articles - 6.99%)
4. Elections (47 articles - 4.56%)
5. 2024 Presidential Election (45 articles - 4.37%)

**Qatar Coverage (Al Jazeera)**
1. Middle-East (36 articles - 44.44%)
2. World News (16 articles - 19.75%)
3. Joe Biden (3 articles)
4. Terrorism (3 articles)
5. Russia (3 articles)

### Temporal Trends

- **Peak Year**: 2024 with 1,785 articles
- **Average Articles per Outlet**: 36.5
- **Median Articles per Outlet**: 2.0
- **Most Outlets**: USA with 286 unique outlets
- **UK Outlets**: Only 6, but high coverage (171.7 articles per outlet on average)

### Notable Patterns

1. **USA Bias Polarization**: Nearly equal split between right-leaning (29.50%) and left-leaning (29.59%) outlets, with minimal center coverage (8.61%)

2. **UK Balance**: Strong preference for center (59.51%) and left (27.96%) bias, with minimal right-bias (12.43%)

3. **Topic Focus by Country**:
   - USA: Domestic politics and elections dominate
   - UK: More global focus with World News as #1 topic
   - Qatar: Heavy Middle-East focus (44.44% of coverage)

4. **Outlet Concentration**: Few outlets (297 total) produce vast amounts of content, with Fox News Digital alone accounting for 1,707 articles

5. **Bias-Topic Correlation**: 
   - Right-leaning outlets focus on politics and elections
   - Leaning-left outlets also focus on politics but with different angle
   - Center outlets provide more balanced coverage across topics

## Geographic Outlet Mapping

### United States (286 outlets)
Major outlets:
- Conservative: Fox News Digital, Washington Examiner, Breitbart, The Daily Wire
- Liberal: CNN, MSNBC, HuffPost, Salon
- Center: Associated Press, Reuters, NPR

### United Kingdom (6 outlets)
Major outlets:
- Conservative: Daily Mail
- Liberal: The Guardian, BBC News
- Center: BBC News, Reuters

### International
- **Qatar**: Al Jazeera (Leaning-left on international news)
- **Germany**: DW (Deutsche Welle)
- **France**: France 24
- **Europe**: Euronews
- **Canada**: CBC News, CTV News, Globe and Mail
- **Australia**: Sydney Morning Herald

## Analysis Methodology

1. **Data Loading**: All 10,832 articles loaded and processed
2. **Geographic Classification**: News outlets manually mapped to their countries of origin
3. **Bias Categorization**: Articles classified into 5 bias categories (original dataset)
4. **Topic Analysis**: 65 distinct topics identified and analyzed
5. **Temporal Analysis**: Date-based trends analyzed across 12 years
6. **Visualization**: Multiple chart types used (bar, pie, heatmap, line, stacked) for different insights

## Technical Details

**Libraries Used**
- `pandas`: Data manipulation and analysis
- `numpy`: Numerical computations
- `matplotlib`: Visualization framework
- `seaborn`: Statistical data visualization

## Recommendations for Further Analysis

1. **Sentiment Analysis**: Analyze article sentiment alongside bias classification
2. **Language Processing**: NLP analysis of article content for bias indicators
3. **Outlet Owner Analysis**: Trace ownership chains to understand corporate bias patterns
4. **Trending Topics**: Identify which outlets break stories first
5. **Fact-Check Integration**: Correlate bias with fact-check accuracy
6. **Reader Demographics**: Connect outlets to reader geography and demographics
7. **Machine Learning Models**: Train classifiers to predict bias from article content

## Dataset Citation

**Source**: Kaggle News Articles For Political Bias Classification
- Contains news articles with political bias labels
- Spans from 2014 to 2025
- Multiple outlets from various countries
- Original dataset structure:
  - `url`: Article URL
  - `topic`: Article topic category
  - `date`: Publication date
  - `title`: Article title
  - `site`: News outlet name
  - `bias`: Political bias classification
  - `page_text`: Article content

**Total Data Analyzed**: 10,832 articles from 297 news outlets in 6 countries


