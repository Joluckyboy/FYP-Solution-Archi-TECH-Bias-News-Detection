"""
Comprehensive News Bias Dataset Analysis and Visualization

This script analyzes the Kaggle News Articles For Political Bias Classification dataset
and generates multiple visualizations including:
- Geographic distribution of news outlets
- Bias distribution by outlet and topic
- Topic coverage analysis
- Time-series trends
- Heatmaps of bias-topic relationships
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ============================================================================
# 1. LOAD AND PREPARE DATA
# ============================================================================

print("Loading dataset...")
df = pd.read_csv('./Kaggle News Articles For Political Bias Classification.csv')

# Convert date column to datetime
df['date'] = pd.to_datetime(df['date'])

print(f"Dataset shape: {df.shape}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")

# ============================================================================
# 2. GEOGRAPHIC MAPPING OF NEWS OUTLETS
# ============================================================================

# Comprehensive mapping of major news outlets to countries
outlet_geography = {
    # United States
    'Fox News Digital': 'USA',
    'CNN Digital': 'USA',
    'NBC News Digital': 'USA',
    'USA TODAY': 'USA',
    'Washington Examiner': 'USA',
    'HuffPost': 'USA',
    'Townhall': 'USA',
    'NPR (Online News)': 'USA',
    'Fox Business': 'USA',
    'Breitbart News': 'USA',
    'CBS News (Online)': 'USA',
    'Forbes': 'USA',
    'ABC News (Online)': 'USA',
    'Daily Beast': 'USA',
    'The Daily Wire': 'USA',
    'CBN': 'USA',
    'New York Post (News)': 'USA',
    'The Blaze': 'USA',
    'Newsmax': 'USA',
    'AP News': 'USA',
    'Associated Press': 'USA',
    'MSNBC': 'USA',
    'Axios': 'USA',
    'Reuters': 'UK',  # International but UK-based
    'WSJ': 'USA',
    'Wall Street Journal': 'USA',
    'Time': 'USA',
    'The Atlantic': 'USA',
    'The Washington Post (Online)': 'USA',
    'Washington Post': 'USA',
    'The Root': 'USA',
    'Slate': 'USA',
    'Salon': 'USA',
    'Reason': 'USA',
    'National Review': 'USA',
    'The National Interest': 'USA',
    'RedState': 'USA',
    'Vox': 'USA',
    'Politico': 'USA',
    'The Hill': 'USA',
    'New York Times (Online News)': 'USA',
    'New York Times': 'USA',
    'Los Angeles Times': 'USA',
    'Chicago Tribune': 'USA',
    'Boston Globe': 'USA',
    'The Guardian': 'UK',
    'BBC News': 'UK',
    'Daily Mail': 'UK',
    'The Telegraph': 'UK',
    'The Independent': 'UK',
    'The Sun': 'UK',
    'Sky News': 'UK',
    'Al Jazeera': 'Qatar',
    'DW (English)': 'Germany',
    'France 24': 'France',
    'Euronews': 'Europe',
    'The Irish Times': 'Ireland',
    'CBC News': 'Canada',
    'CTV News': 'Canada',
    'Toronto Star': 'Canada',
    'The Globe and Mail': 'Canada',
    'Sydney Morning Herald': 'Australia',
    'ABC News (Australian)': 'Australia',
    'The Australian': 'Australia',
    'News Corp Australia': 'Australia',
    'Stuff.co.nz': 'New Zealand',
    'NZ Herald': 'New Zealand',
    'India Today': 'India',
    'Times of India': 'India',
    'The Hindu': 'India',
    'NDTV': 'India',
    'Business Insider': 'USA',
    'Quartz': 'USA',
    'Insider': 'USA',
    'The Verge': 'USA',
    'Wired': 'USA',
    'Mashable': 'USA',
    'TechCrunch': 'USA',
    'CNBC': 'USA',
    'MarketWatch': 'USA',
    'Yahoo News': 'USA',
    'The Daily': 'USA',
    'Newsweek': 'USA',
    'U.S. News & World Report': 'USA',
    'Daily Caller': 'USA',
    'Epoch Times': 'USA',
    'The Federalist': 'USA',
    'Conservative Review': 'USA',
    'Free Beacon': 'USA',
    'Examiner.com': 'USA',
    'WND': 'USA',
    'Breitbart': 'USA',
    'Red State': 'USA',
    'The American Conservative': 'USA',
    'Real Clear Politics': 'USA',
    'Heritage': 'USA',
    'American Enterprise Institute': 'USA',
    'Center for American Progress': 'USA',
    'Think Progress': 'USA',
    'Media Matters': 'USA',
    'CNN': 'USA',
    'MSNBC Digital': 'USA',
    'Fox': 'USA',
    'ABC': 'USA',
    'CBS': 'USA',
    'NBC': 'USA',
    'PBS': 'USA',
}

# Create a function to map outlets to countries
def get_country(outlet):
    """Get country for a news outlet, default to USA for unknown outlets"""
    return outlet_geography.get(outlet, 'USA')

# Add country column
df['country'] = df['site'].apply(get_country)

print(f"\nNews outlets by country:")
print(df['country'].value_counts())

# ============================================================================
# 3. CREATE VISUALIZATIONS
# ============================================================================

# Create a figure with subplots
fig = plt.figure(figsize=(20, 24))

# -----------------------------------------------------------------------
# PLOT 1: News Articles Distribution by Country (Geographic)
# -----------------------------------------------------------------------
ax1 = plt.subplot(4, 3, 1)
country_counts = df['country'].value_counts()
colors = plt.cm.Set3(np.linspace(0, 1, len(country_counts)))
country_counts.plot(kind='barh', ax=ax1, color=colors, edgecolor='black')
ax1.set_xlabel('Number of Articles', fontsize=11, fontweight='bold')
ax1.set_ylabel('Country', fontsize=11, fontweight='bold')
ax1.set_title('News Articles Distribution by Geographic Location', 
              fontsize=12, fontweight='bold', pad=15)
ax1.grid(axis='x', alpha=0.3)
for i, v in enumerate(country_counts.values):
    ax1.text(v + 50, i, str(v), va='center', fontweight='bold')

# -----------------------------------------------------------------------
# PLOT 2: Top 20 News Outlets by Article Count
# -----------------------------------------------------------------------
ax2 = plt.subplot(4, 3, 2)
top_outlets = df['site'].value_counts().head(20)
colors_outlets = plt.cm.Spectral(np.linspace(0, 1, len(top_outlets)))
top_outlets.plot(kind='barh', ax=ax2, color=colors_outlets, edgecolor='black')
ax2.set_xlabel('Number of Articles', fontsize=11, fontweight='bold')
ax2.set_ylabel('News Outlet', fontsize=11, fontweight='bold')
ax2.set_title('Top 20 News Outlets by Article Count', 
              fontsize=12, fontweight='bold', pad=15)
ax2.grid(axis='x', alpha=0.3)
for i, v in enumerate(top_outlets.values):
    ax2.text(v + 10, i, str(v), va='center', fontweight='bold', fontsize=9)

# -----------------------------------------------------------------------
# PLOT 3: Bias Distribution Across All Articles
# -----------------------------------------------------------------------
ax3 = plt.subplot(4, 3, 3)
bias_counts = df['bias'].value_counts()
colors_bias = {'left': '#FF6B6B', 'leaning-left': '#FF8E8E', 
               'center': '#95E1D3', 'leaning-right': '#A8D8FF', 'right': '#4A90E2'}
colors_list = [colors_bias.get(bias, '#CCCCCC') for bias in bias_counts.index]
wedges, texts, autotexts = ax3.pie(bias_counts.values, labels=bias_counts.index, 
                                     autopct='%1.1f%%', colors=colors_list, 
                                     startangle=90, textprops={'fontweight': 'bold'})
ax3.set_title('Overall Bias Distribution in News Articles', 
              fontsize=12, fontweight='bold', pad=15)
for autotext in autotexts:
    autotext.set_color('black')
    autotext.set_fontsize(10)

# -----------------------------------------------------------------------
# PLOT 4: Top 15 Topics Coverage
# -----------------------------------------------------------------------
ax4 = plt.subplot(4, 3, 4)
top_topics = df['topic'].value_counts().head(15)
colors_topics = plt.cm.tab20(np.linspace(0, 1, len(top_topics)))
top_topics.plot(kind='barh', ax=ax4, color=colors_topics, edgecolor='black')
ax4.set_xlabel('Number of Articles', fontsize=11, fontweight='bold')
ax4.set_ylabel('Topic', fontsize=11, fontweight='bold')
ax4.set_title('Top 15 News Topics Covered', 
              fontsize=12, fontweight='bold', pad=15)
ax4.grid(axis='x', alpha=0.3)
for i, v in enumerate(top_topics.values):
    ax4.text(v + 5, i, str(v), va='center', fontweight='bold', fontsize=9)

# -----------------------------------------------------------------------
# PLOT 5: Bias Distribution by Country
# -----------------------------------------------------------------------
ax5 = plt.subplot(4, 3, 5)
bias_country = pd.crosstab(df['country'], df['bias'])
bias_country.plot(kind='bar', ax=ax5, stacked=True, 
                  color=[colors_bias.get(b, '#CCCCCC') for b in bias_country.columns],
                  edgecolor='black', width=0.7)
ax5.set_xlabel('Country', fontsize=11, fontweight='bold')
ax5.set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
ax5.set_title('Bias Distribution by Geographic Location', 
              fontsize=12, fontweight='bold', pad=15)
ax5.legend(title='Bias Type', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
ax5.tick_params(axis='x', rotation=45)
ax5.grid(axis='y', alpha=0.3)

# -----------------------------------------------------------------------
# PLOT 6: Bias vs Topic Heatmap (Top Topics)
# -----------------------------------------------------------------------
ax6 = plt.subplot(4, 3, 6)
top_topics_list = df['topic'].value_counts().head(10).index
bias_topic_matrix = pd.crosstab(df[df['topic'].isin(top_topics_list)]['topic'], 
                                 df[df['topic'].isin(top_topics_list)]['bias'])
# Reorder columns for better visualization
bias_order = ['left', 'leaning-left', 'center', 'leaning-right', 'right']
bias_topic_matrix = bias_topic_matrix[[col for col in bias_order if col in bias_topic_matrix.columns]]

sns.heatmap(bias_topic_matrix, annot=True, fmt='d', cmap='RdYlGn_r', ax=ax6,
            cbar_kws={'label': 'Article Count'}, linewidths=0.5)
ax6.set_xlabel('Bias Type', fontsize=11, fontweight='bold')
ax6.set_ylabel('Topic', fontsize=11, fontweight='bold')
ax6.set_title('Heatmap: Bias Type vs Top 10 Topics', 
              fontsize=12, fontweight='bold', pad=15)
ax6.tick_params(axis='x', rotation=45)
ax6.tick_params(axis='y', rotation=0)

# -----------------------------------------------------------------------
# PLOT 7: Articles Over Time (Monthly Trend)
# -----------------------------------------------------------------------
ax7 = plt.subplot(4, 3, 7)
df['year_month'] = df['date'].dt.to_period('M')
monthly_counts = df.groupby('year_month').size()
monthly_counts.index = monthly_counts.index.to_timestamp()
ax7.plot(monthly_counts.index, monthly_counts.values, linewidth=2, marker='o', markersize=4)
ax7.fill_between(monthly_counts.index, monthly_counts.values, alpha=0.3)
ax7.set_xlabel('Date', fontsize=11, fontweight='bold')
ax7.set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
ax7.set_title('Article Count Trend Over Time (Monthly)', 
              fontsize=12, fontweight='bold', pad=15)
ax7.grid(True, alpha=0.3)
ax7.tick_params(axis='x', rotation=45)

# -----------------------------------------------------------------------
# PLOT 8: Articles by Year
# -----------------------------------------------------------------------
ax8 = plt.subplot(4, 3, 8)
yearly_counts = df.groupby(df['date'].dt.year).size()
colors_year = plt.cm.viridis(np.linspace(0, 1, len(yearly_counts)))
yearly_counts.plot(kind='bar', ax=ax8, color=colors_year, edgecolor='black')
ax8.set_xlabel('Year', fontsize=11, fontweight='bold')
ax8.set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
ax8.set_title('Articles Distribution by Year', 
              fontsize=12, fontweight='bold', pad=15)
ax8.grid(axis='y', alpha=0.3)
ax8.tick_params(axis='x', rotation=45)
for i, v in enumerate(yearly_counts.values):
    ax8.text(i, v + 50, str(v), ha='center', fontweight='bold', fontsize=9)

# -----------------------------------------------------------------------
# PLOT 9: Bias Trend Over Time (Yearly)
# -----------------------------------------------------------------------
ax9 = plt.subplot(4, 3, 9)
bias_yearly = pd.crosstab(df['date'].dt.year, df['bias'])
bias_yearly_pct = bias_yearly.div(bias_yearly.sum(axis=1), axis=0) * 100
bias_yearly_pct.plot(ax=ax9, marker='o', linewidth=2,
                     color=[colors_bias.get(b, '#CCCCCC') for b in bias_yearly_pct.columns])
ax9.set_xlabel('Year', fontsize=11, fontweight='bold')
ax9.set_ylabel('Percentage of Articles (%)', fontsize=11, fontweight='bold')
ax9.set_title('Bias Trend Over Years (Percentage)', 
              fontsize=12, fontweight='bold', pad=15)
ax9.legend(title='Bias Type', fontsize=9, title_fontsize=10)
ax9.grid(True, alpha=0.3)

# -----------------------------------------------------------------------
# PLOT 10: Top 15 Outlets - Bias Distribution (Stacked Bar)
# -----------------------------------------------------------------------
ax10 = plt.subplot(4, 3, 10)
top_15_outlets = df['site'].value_counts().head(15).index
outlet_bias = pd.crosstab(df[df['site'].isin(top_15_outlets)]['site'], 
                           df[df['site'].isin(top_15_outlets)]['bias'])
outlet_bias = outlet_bias[[col for col in bias_order if col in outlet_bias.columns]]
outlet_bias.plot(kind='barh', ax=ax10, stacked=True,
                 color=[colors_bias.get(b, '#CCCCCC') for b in outlet_bias.columns],
                 edgecolor='black')
ax10.set_xlabel('Number of Articles', fontsize=11, fontweight='bold')
ax10.set_ylabel('News Outlet', fontsize=11, fontweight='bold')
ax10.set_title('Bias Distribution in Top 15 Outlets', 
               fontsize=12, fontweight='bold', pad=15)
ax10.legend(title='Bias Type', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
ax10.grid(axis='x', alpha=0.3)

# -----------------------------------------------------------------------
# PLOT 11: Topic Distribution by Bias Type
# -----------------------------------------------------------------------
ax11 = plt.subplot(4, 3, 11)
top_10_topics = df['topic'].value_counts().head(10).index
topic_bias = pd.crosstab(df[df['topic'].isin(top_10_topics)]['bias'],
                          df[df['topic'].isin(top_10_topics)]['topic'])
topic_bias.plot(kind='bar', ax=ax11, stacked=False, width=0.8,
                color=plt.cm.tab20(np.linspace(0, 1, len(topic_bias.columns))),
                edgecolor='black')
ax11.set_xlabel('Bias Type', fontsize=11, fontweight='bold')
ax11.set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
ax11.set_title('Top 10 Topics Distribution by Bias Type', 
               fontsize=12, fontweight='bold', pad=15)
ax11.legend(title='Topic', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
ax11.tick_params(axis='x', rotation=45)
ax11.grid(axis='y', alpha=0.3)

# -----------------------------------------------------------------------
# PLOT 12: Month Distribution (Aggregated Across All Years)
# -----------------------------------------------------------------------
ax12 = plt.subplot(4, 3, 12)
monthly_agg = df.groupby(df['date'].dt.month).size()
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
colors_month = plt.cm.cool(np.linspace(0, 1, 12))
ax12.bar(range(1, 13), monthly_agg.values, color=colors_month, edgecolor='black')
ax12.set_xlabel('Month', fontsize=11, fontweight='bold')
ax12.set_ylabel('Total Articles (All Years)', fontsize=11, fontweight='bold')
ax12.set_title('Seasonal Patterns: Articles by Month', 
               fontsize=12, fontweight='bold', pad=15)
ax12.set_xticks(range(1, 13))
ax12.set_xticklabels(month_names, rotation=45)
ax12.grid(axis='y', alpha=0.3)
for i, v in enumerate(monthly_agg.values):
    ax12.text(i+1, v + 20, str(v), ha='center', fontweight='bold', fontsize=9)

plt.tight_layout()
plt.savefig('news_bias_analysis_comprehensive.png', dpi=300, bbox_inches='tight')
print("\n✓ Comprehensive visualization saved as 'news_bias_analysis_comprehensive.png'")
plt.close()

# # ============================================================================
# # 4. ADDITIONAL ANALYSIS: OUTLET-COUNTRY-BIAS-TOPIC RELATIONSHIP
# # ============================================================================

print("\n" + "="*80)
print("DETAILED ANALYSIS: NEWS OUTLETS BY COUNTRY, BIAS, AND TOPIC")
print("="*80)

# Create detailed summary
summary_df = df.groupby(['country', 'site', 'bias']).size().reset_index(name='count')
summary_df = summary_df.sort_values(['country', 'count'], ascending=[True, False])

print("\nTop Outlets by Country and Their Bias Distribution:")
print("-" * 80)

for country in summary_df['country'].unique():
    country_data = summary_df[summary_df['country'] == country]
    print(f"\n{country.upper()}")
    print("-" * 40)
    for outlet in country_data['site'].unique()[:5]:  # Top 5 outlets per country
        outlet_data = country_data[country_data['site'] == outlet]
        print(f"  {outlet}:")
        for idx, row in outlet_data.iterrows():
            print(f"    - {row['bias']}: {row['count']} articles")

# # ============================================================================
# # 5. SUMMARY STATISTICS
# # ============================================================================

print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

print(f"\nTotal Articles: {len(df):,}")
print(f"Date Range: {df['date'].min().date()} to {df['date'].max().date()}")
print(f"Total Years Covered: {df['date'].dt.year.max() - df['date'].dt.year.min() + 1}")
print(f"\nUnique Outlets: {df['site'].nunique()}")
print(f"Countries Represented: {df['country'].nunique()}")
print(f"Unique Topics: {df['topic'].nunique()}")
print(f"Bias Categories: {df['bias'].nunique()}")

print(f"\n{'Bias Distribution:':^40}")
print("-" * 40)
for bias_type, count in df['bias'].value_counts().items():
    pct = (count / len(df)) * 100
    print(f"{bias_type:20} {count:6,} ({pct:5.2f}%)")

print(f"\n{'Top 5 Countries:':^40}")
print("-" * 40)
for country, count in df['country'].value_counts().head(5).items():
    pct = (count / len(df)) * 100
    print(f"{country:20} {count:6,} ({pct:5.2f}%)")

print(f"\n{'Top 5 Topics:':^40}")
print("-" * 40)
for topic, count in df['topic'].value_counts().head(5).items():
    pct = (count / len(df)) * 100
    print(f"{topic:20} {count:6,} ({pct:5.2f}%)")

# ============================================================================
# 6. EXPORT DETAILED DATA FOR REFERENCE
# ============================================================================

# Create comprehensive outlet summary
outlet_summary = df.groupby(['country', 'site']).agg({
    'bias': lambda x: x.value_counts().to_dict(),
    'topic': 'nunique',
    'date': ['min', 'max', 'count']
}).reset_index()
outlet_summary.columns = ['Country', 'Outlet', 'Bias Distribution', 
                          'Unique Topics', 'First Article', 'Last Article', 'Total Articles']
outlet_summary = outlet_summary.sort_values('Total Articles', ascending=False)

# Save to CSV
outlet_summary.to_csv('news_outlets_summary.csv', index=False)
print("\n✓ Detailed outlet summary saved as 'news_outlets_summary.csv'")

print("\n" + "="*80)
print("ANALYSIS COMPLETE!")
print("="*80)
print("\nGenerated Files:")
print("  1. news_bias_analysis_comprehensive.png - Main visualization with 12 plots")
print("  2. news_outlets_summary.csv - Detailed outlet information")
print("\n" + "="*80)
