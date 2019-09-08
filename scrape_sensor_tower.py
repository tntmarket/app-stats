import itertools

import csv
import json
from typing import Dict
from urllib import request

TODAY = '2019-09-08'

CATEGORY_BY_ID = {
    6018: 'Books',
    6000: 'Business',
    6017: 'Education',
    6016: 'Entertainment',
    6015: 'Finance',
    6023: 'Food & Drink',
    6014: 'Games',
    6013: 'Health & Fitness',
    6011: 'Music',
    6010: 'Navigation',
    6009: 'News',
    6008: 'Photo & Video',
    6007: 'Productivity',
    6006: 'Reference',
    6005: 'Social Networking',
    6024: 'Shopping',
    6004: 'Sports',
    6001: 'Weather',
}


def category_by_id(category_id):
    if category_id in CATEGORY_BY_ID:
        return CATEGORY_BY_ID[category_id]
    else:
        return 'Other'


def sensor_tower_url(category_id=6018):
    return 'https://sensortower.com/api/ios/rankings/get_category_rankings?category={category_id}&country=US&date={date}&device=IPHONE&limit=50&offset=0'.format(
        category_id=category_id,
        date=TODAY,
    )


def scrape_category(category_id):
    url = request.urlopen(sensor_tower_url(category_id))
    ranking_stats = json.loads(url.read())
    return {
        app['app_id']: extract_interesting_fields(app)
        for app in flatten_ranks(ranking_stats)
    }


def scrape_all_categories() -> Dict[int, Dict]:
    app_stats = {}
    for category_id, category in CATEGORY_BY_ID.items():
        print('Scraping {}...'.format(category))
        app_stats.update(scrape_category(category_id))
    return app_stats


def flatten_ranks(ranking_stats):
    """For some reason sensor tower presents data like:
    [
        [rank1Free, rank1Paid, rank1Grossing],
        [rank2Free, rank2Paid, rank2Grossing],
        # etc.
    ]

    This flattens app stats into one list
    """
    return itertools.chain.from_iterable(ranking_stats)


def extract_interesting_fields(app):
    return {
        # About
        'id': app['id'],
        'name': app['name'],
        'categories': [
            category_by_id(category_id)
            for category_id in app['categories']
        ],
        'url': app['url'],
        # Quality
        'rating': app['rating'],
        'ratings_total': app['global_rating_count'],
        'ratings_current_version': app['rating_count_for_current_version'],
        # Revenue
        'monthly_downloads': app['humanized_worldwide_last_month_downloads']['downloads'],
        'monthly_revenue': (
            # break ties between revenue estimates using rank
            app['humanized_worldwide_last_month_revenue']['revenue'] - app['rank']
        ),
        # Miscellaneous
        'buys_ads': app['buys_ads'],
        'shows_ads': app['shows_ads'],
    }


all_stats = scrape_all_categories()


with open('sensor_tower_stats.csv', 'w', newline='') as report_file:
    first_app = next(iter(all_stats.values()))
    report_writer = csv.DictWriter(report_file, fieldnames=first_app.keys())

    report_writer.writeheader()
    for app in all_stats.values():
        report_writer.writerow(app)
