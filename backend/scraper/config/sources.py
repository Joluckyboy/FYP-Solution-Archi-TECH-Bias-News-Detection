"""
News source configurations for scraping
"""

SINGAPORE_SOURCES = {
    'cna': {
        'url': 'https://www.channelnewsasia.com/singapore',
        'name': 'Channel NewsAsia',
        'country': 'Singapore',
        'type': 'custom'
    },
    'straits': {
        'url': 'https://www.straitstimes.com/singapore/latest',
        'name': 'The Straits Times',
        'country': 'Singapore',
        'type': 'custom'
    },
    'todayonline': {
        'url': 'https://www.todayonline.com/singapore',
        'name': 'TODAY Online',
        'country': 'Singapore',
        'type': 'generic'
    },
    'business_times': {
        'url': 'https://www.businesstimes.com.sg/singapore',
        'name': 'The Business Times',
        'country': 'Singapore',
        'type': 'generic'
    },
    'mothership': {
        'url': 'https://mothership.sg/news/',
        'name': 'Mothership',
        'country': 'Singapore',
        'type': 'generic'
    },
    'yahoo_sg': {
        'url': 'https://sg.news.yahoo.com/',
        'name': 'Yahoo News Singapore',
        'country': 'Singapore',
        'type': 'generic'
    },
}

US_SOURCES = {
    'cnn': {
        'url': 'https://www.cnn.com',
        'name': 'CNN',
        'country': 'United States',
        'type': 'generic'
    },
    'foxnews': {
        'url': 'https://www.foxnews.com',
        'name': 'Fox News',
        'country': 'United States',
        'type': 'custom'
    },
    'washingtonpost': {
        'url': 'https://www.washingtonpost.com',
        'name': 'The Washington Post',
        'country': 'United States',
        'type': 'generic'
    },
    'nbcnews': {
        'url': 'https://www.nbcnews.com',
        'name': 'NBC News',
        'country': 'United States',
        'type': 'generic'
    },
    'usatoday': {
        'url': 'https://www.usatoday.com/news/',
        'name': 'USA Today',
        'country': 'United States',
        'type': 'generic'
    },
    'npr': {
        'url': 'https://www.npr.org/sections/news/',
        'name': 'NPR',
        'country': 'United States',
        'type': 'generic'
    },
}
