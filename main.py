import flask
from flask import request, jsonify, render_template, url_for
import requests
import json
from datetime import datetime
import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from difflib import SequenceMatcher
from operator import itemgetter



app = flask.Flask(__name__)

# Fetch User's Anime List
def fetch_all_anime_data(base_url, headers, params):
    anime_list = []
    next_url = base_url  # Start with the base URL

    while next_url:
        # Make the API request
        response = requests.get(next_url, headers=headers, params=params if next_url == base_url else None)
        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code}, {response.json()}")
            break

        data = response.json()
        anime_list.extend(data.get("data", []))  # Add current page data to the list

        # Update the next URL from the paging info
        next_url = data.get("paging", {}).get("next")

        print(f"Fetched {len(data.get('data', []))} items. Total so far: {len(anime_list)}")

    return anime_list

# Example function to filter anime based on start_date
def filter_anime_by_start_date(anime_list, target_year):
    filtered_anime = []
    for anime in anime_list:
        # Extract the start_date from list_status, if it exists
        start_date = anime.get("list_status", {}).get("start_date", None)
        if not start_date:
            continue  # Skip if start_date is not present
        
        try:
            # Parse the date to check if it's in the target year
            # Handle both `YYYY` and `YYYY-MM-DD` formats
            if len(start_date) == 4:  # If format is `YYYY`
                year = int(start_date)
            else:
                year = datetime.strptime(start_date[:10], "%Y-%m-%d").year
            
            if year == target_year:
                filtered_anime.append(anime)
        except ValueError:
            continue  # Skip if date parsing fails

    return filtered_anime

# fetch anime details
def fetch_anime_details(all_anime):
    """
    Fetch detailed information for a list of anime entries.

    Args:
        all_anime (list): A list of anime entries, where each entry contains
                          details including 'node' and 'list_status'.

    Returns:
        list: A list of dictionaries containing detailed information for each anime.
    """
    details = []
    
    for entry in all_anime:
        try:
            # Extract anime ID and fetch data from the API
            anime_id = entry['node']['id']
            
            url = f'https://api.jikan.moe/v4/anime/{anime_id}'
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for HTTP request issues
            
            data = response.json()

            # Extract genres, themes, and demographics
            genres = [genre['name'] for genre in data['data']['genres']]
            themes = [theme['name'] for theme in data['data']['themes']]
            demographics = [demographic['name'] for demographic in data['data']['demographics']]

            # Extract start date if available
            start_date = entry['list_status'].get('start_date', "Unknown")

            # Compile the anime details
            details.append({
                'title': data['data']['title'],
                'score': entry['list_status']['score'],
                'status': entry['list_status']['status'],
                'start_date': start_date,
                'genres': genres,
                'studio': data['data']['studios'][0]['name'] if data['data']['studios'] else "Unknown",
                'rating': data['data']['score'],
                'themes': themes,
                'demographics': demographics,
                'rank': data['data'].get('rank', "Unranked"),
                'popularity': data['data'].get('popularity', "Unknown"),
                'episodes': entry['list_status']['num_episodes_watched']
            })

            
            # Pause to respect API rate limits
            time.sleep(1)
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching details for Anime ID {anime_id}: {e}")
        except KeyError as e:
            print(f"Key error in response data for Anime ID {anime_id}: {e}")
        except Exception as e:
            print(f"Unexpected error for Anime ID {anime_id}: {e}")
    
    return details

# 
def extract_genres(all_anime):
    genre_counts = {}
    for anime in all_anime:
        for genre in anime["genres"]:
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
    return genre_counts  # Ensure the function returns the genre counts

def extract_themes(all_anime):
    theme_counts = {}
    for anime in all_anime:
        for genre in anime["themes"]:
            theme_counts[genre] = theme_counts.get(genre, 0) + 1
    return theme_counts

# Plotting the genre distribution
def plot_genre_distribution(genre_counts):
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    genres, counts = zip(*sorted_genres)
    
    plt.figure(figsize=(12, 6))
    plt.bar(genres, counts)
    plt.xlabel("Genres")
    plt.ylabel("Number of Anime")
    plt.title("Genre Distribution of Anime in 2024")
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.tight_layout()
    plt.savefig("static/images/genre_distribution.png")

def plot_theme_distribution(theme_counts):
    sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
    themes, counts = zip(*sorted_themes)
    
    plt.figure(figsize=(20, 6))
    plt.bar(themes, counts)
    plt.xlabel("Themes")
    plt.ylabel("Number of Anime")
    plt.title("Theme Distribution of Anime in 2024")
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.tight_layout()
    plt.savefig("static/images/theme_distribution.png")

# Extract demographics and plot the distribution
def extract_demographics(all_anime):
    demographic_counts = {}
    for anime in all_anime:
        for demographic in anime["demographics"]:
            demographic_counts[demographic] = demographic_counts.get(demographic, 0) + 1
    return demographic_counts

def plot_demographic_distribution(demographic_counts):
    sorted_demographics = sorted(demographic_counts.items(), key=lambda x: x[1], reverse=True)
    demographics, counts = zip(*sorted_demographics)
    
    plt.figure(figsize=(20, 6))
    plt.bar(demographics, counts)
    plt.xlabel("Demographics")
    plt.ylabel("Number of Anime")
    plt.title("Demographic Distribution of Anime in 2024")
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.tight_layout()
    plt.savefig("static/images/demographic_distribution.png")

# Extract studios and plot the distribution
def extract_studios(all_anime):
    studio_counts = {}
    for anime in all_anime:
        studio = anime["studio"]
        studio_counts[studio] = studio_counts.get(studio, 0) + 1
    return studio_counts

def plot_studio_distribution(studio_counts):
    sorted_studios = sorted(studio_counts.items(), key=lambda x: x[1], reverse=True)
    studios, counts = zip(*sorted_studios)
    
    plt.figure(figsize=(20, 6))
    plt.bar(studios, counts)
    plt.xlabel("Studios")
    plt.ylabel("Number of Anime")
    plt.title("Studio Distribution of Anime in 2024")
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.tight_layout()
    plt.savefig("static/images/studio_distribution.png")

# make Area plot between score and rating
def get_score_rating(all_anime):
    filtered_anime = [anime for anime in all_anime if anime["score"] is not None and anime["rating"] is not None]

    # Extracting scores, ratings, and titles
    titles = [anime["title"] for anime in filtered_anime]
    scores = [anime["score"] for anime in filtered_anime]
    ratings = [anime["rating"] for anime in filtered_anime]
    i=0
    scoreVsRating = []
    for i in range(len(titles)):
        scoreVsRating.append({
            "title": titles[i],
            "my_score": scores[i],
            "overall_rating": ratings[i]
    })
    return scoreVsRating

def create_area_chart(data, output_filename="static/images/score_vs_rating.png"):
    titles = [' '.join(item['title'].split()[:3]) for item in data]  # Get the first three words of each title
    my_scores = [item['my_score'] for item in data]
    overall_ratings = [item['overall_rating'] for item in data]
    # Create the plot with a wider figure size
    plt.figure(figsize=(20, 6))  # Increase the width to 20 for better spacing
    plt.fill_between(titles, my_scores, label="My Scores", alpha=0.5, color="blue")
    plt.fill_between(titles, overall_ratings, label="Overall Ratings", alpha=0.5, color="green")
    # Customize the plot
    plt.title("Area Chart of My Scores vs. Overall Ratings", fontsize=14)
    plt.xlabel("Titles", fontsize=12)
    plt.ylabel("Scores", fontsize=12)
    plt.xticks(rotation=45, ha='right', fontsize=8)  # Rotate x-axis labels and reduce font size for readability
    plt.legend()
    plt.grid(alpha=0.3)

    # Save as an image
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    plt.close()  # Close the plot to free up memory

def filter_similar_anime(anime_list):
    filtered_list = []
    for anime in anime_list:
        if not any(SequenceMatcher(None, anime, existing).ratio() > 0.70 for existing in filtered_list):
            filtered_list.append(anime)
    return filtered_list

# find the least popular completed anime watched
def least_popular_anime(all_anime):
    completed_anime = [anime for anime in all_anime if anime["status"] == "completed"]
    completed_anime.sort(key=lambda x: x["popularity"])
    return completed_anime[-1]

def find_watchtime(all_anime):
    df = pd.json_normalize(all_anime)
    df['watchtime'] = df['episodes'].dropna() * 24
    watchtime = df['watchtime'].sum()
    return watchtime

def average_score(all_anime):
    df = pd.json_normalize(all_anime)
    # Filter rows where status is 'completed'
    completed_anime = df[df['status'] == 'completed']
    # Calculate averages
    avg_score = round(completed_anime['score'].mean(), 2) if not completed_anime.empty else 0
    avg_rating = round(completed_anime['rating'].mean(), 2) if not completed_anime.empty else 0   
    return avg_score, avg_rating

# anime watch monthly
def anime_watch_monthly(all_anime):
    df = pd.json_normalize(all_anime)
    # Ensure all dates are strings
    df['start_date'] = df['start_date'].astype(str)   
    # Standardize date format
    df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')  
    # Extract the month
    df['month'] = df['start_date'].dt.month   
    # Group by month and count
    monthly_anime = df.groupby('month').size()
    
    return monthly_anime

def anime_watch_trend(monthly_anime, monthly_data_rolling):
    plt.figure(figsize=(20, 6))
    plt.plot(monthly_anime.index.astype(str), monthly_data_rolling, marker='o', label='Monthly Watch Trend')
    plt.title('Anime Watching Trend')
    plt.xlabel('Month')
    plt.ylabel('Number of Episodes Watched')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.savefig('static/images/anime_watching_trend.png')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_username', methods=['POST'])
def submit_username():
    username = request.form.get('username')
    if not username:
        return "Username is required!", 400

    # Simulate fetching data (replace with actual API call)
    BASE_URL = f"https://api.myanimelist.net/v2/users/{username}/animelist"
    HEADERS = {
        'X-MAL-CLIENT-ID':"a4126bcedef78e592db3e280720a9fa1" # Replace with your access token
    }
    
    # Parameters for the initial request
    PARAMS = {
        "fields": "list_status",  # Fields you want to include in the response      
        "nsfw":"true"
    }
    
    animeList = fetch_all_anime_data(BASE_URL, HEADERS, PARAMS)
    
    # 2024 filtered anime list
    filteredAnimeList = filter_anime_by_start_date(animeList, 2024)

    AllAnime2024 = fetch_anime_details(filteredAnimeList)


    #  Get All Insights
    genre_counts = extract_genres(AllAnime2024)
    theme_counts = extract_themes(AllAnime2024)
    demographic_counts = extract_demographics(AllAnime2024)
    studio_counts = extract_studios(AllAnime2024)
    score_rating = get_score_rating(AllAnime2024)
    create_area_chart(score_rating)
    least_popular = least_popular_anime(AllAnime2024)
    watchtime = find_watchtime(AllAnime2024)
    watchtime = round(watchtime/60, 2)
    total_anime = len(AllAnime2024)
    # Plotting the genre distribution
    plot_genre_distribution(genre_counts)
    plot_theme_distribution(theme_counts)
    plot_demographic_distribution(demographic_counts)
    plot_studio_distribution(studio_counts)
    avg_score, avg_rating = average_score(AllAnime2024)
    genres = dict(sorted(genre_counts.items(), key=itemgetter(1), reverse=True)[:5])
    themes = dict(sorted(theme_counts.items(), key=itemgetter(1), reverse=True)[:5])
    demographics = dict(sorted(demographic_counts.items(), key=itemgetter(1), reverse=True)[:5])
    studios = dict(sorted(studio_counts.items(), key=itemgetter(1), reverse=True)[:5])
    top_anime = [anime['title'] for anime in AllAnime2024 if anime["score"] == 10]
    top_anime = filter_similar_anime(top_anime)
    monthly_anime = anime_watch_monthly(AllAnime2024)
    monthly_data_rolling = monthly_anime.rolling(window=2).mean()
    anime_watch_trend(monthly_anime, monthly_data_rolling)

    scoreRatingUrl = url_for('static', filename='images/score_vs_rating.png')
    studioDistributionUrl = url_for('static', filename='images/studio_distribution.png')
    genreDistributionUrl = url_for('static', filename='images/genre_distribution.png')
    themeDistributionUrl = url_for('static', filename='images/theme_distribution.png')
    demographicDistributionUrl = url_for('static', filename='images/demographic_distribution.png')
    animeWatchingTrendUrl = url_for('static', filename='images/anime_watching_trend.png')

    return render_template('results.html', username=username, top_anime=top_anime, anime_list=AllAnime2024, least_popular=least_popular, watchtime=watchtime, total_anime=total_anime, genres=genres, themes=themes, demographics=demographics, studios=studios, avg_score=avg_score, avg_rating=avg_rating, scoreRatingUrl=scoreRatingUrl, studioDistributionUrl=studioDistributionUrl, genreDistributionUrl=genreDistributionUrl, themeDistributionUrl=themeDistributionUrl, demographicDistributionUrl=demographicDistributionUrl, animeWatchingTrendUrl=animeWatchingTrendUrl)



@app.route('/anime', methods=['GET'])
def get_anime():
    username = request.args.get('username')
    BASE_URL = f"https://api.myanimelist.net/v2/users/{username}/animelist"
    HEADERS = {
        'X-MAL-CLIENT-ID':"your_client_id" # Replace with your access token
    }
    
    # Parameters for the initial request
    PARAMS = {
        "fields": "list_status",  # Fields you want to include in the response      
        "nsfw":"true"
    }
    
    animeList = fetch_all_anime_data(BASE_URL, HEADERS, PARAMS)
    return jsonify(animeList)


if __name__ == "__main__":
    app.run()
