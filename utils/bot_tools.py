
from pydantic import BaseModel, Field
from langchain.agents import tool
import requests
import datetime
import wikipedia

from utils.scrape_method import *
from utils.link_scraper import text_summary

class OpenMeteoInput(BaseModel):
    latitude: float = Field(..., description="Latitude of the location to fetch weather data for")
    longitude: float = Field(..., description="Longitude of the location to fetch weather data for")

@tool(args_schema=OpenMeteoInput)
def get_current_temperature(latitude: float, longitude: float) -> dict:
    """Fetch current temperature for given coordinates."""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Parameters for the request
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': 'temperature_2m',
        'forecast_days': 1,
        'temperature_unit': 'fahrenheit',
    }

    # Make the request
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code == 200:
        results = response.json()
    else:
        raise Exception(f"API Request failed with status code: {response.status_code}")

    current_utc_time = datetime.datetime.utcnow()
    time_list = [datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00')) for time_str in results['hourly']['time']]
    temperature_list = results['hourly']['temperature_2m']
    
    closest_time_index = min(range(len(time_list)), key=lambda i: abs(time_list[i] - current_utc_time))
    current_temperature = temperature_list[closest_time_index]
    
    return f'The current temperature is {current_temperature}°F'


@tool
def lights_on(query: str) -> str:
    """This tools turns the lights on. 
    This command will be used if a user asks to turn on or off the lights.
    If this returns True, the response back will ALWAYS be 'The lights are on'
    If returns false, the response will be 'The lights are off'
    The Query arguments must either be: "turn on the lights" or "turn off the lights"
    """
    if query == 'turn on the lights':
        return f"Lights are on is: True"
    else:
        return f"Lights are off is: True"
    

@tool
def search_wikipedia(query: str) -> str:
    """
    Run Wikipedia search and get page summaries.
    Any request that is specifically asking about a person, place, or thing will be searched on Wikipedia.
    Use this function if there is something in the question that is after your training data.
    """
    page_titles = wikipedia.search(query)
    summaries = []
    for page_title in page_titles[: 3]:
        try:
            wiki_page =  wikipedia.page(title=page_title, auto_suggest=False)
            summaries.append(f"Page: {page_title}\nSummary: {wiki_page.summary}")
        except (
            wikipedia.exceptions.PageError,
            wikipedia.exceptions.DisambiguationError,
        ):
            pass
    if not summaries:
        return "No good Wikipedia Search Result was found"
    return "\n\n".join(summaries)

@tool
def scrape_news(link=None, memory=None) -> str:
    """
    Scrape news from the OCC website.
    Any request that is specifically asking about a person, place, or thing will be searched on Wikipedia.
    First only call the function with link being None.
    Read back the titles ONLY.
    Then call the function with the link being the title you want to read.
    If the link is passed and a text summary is returned, summarize the context.
    """
    if link:
        print("Extracting text from link...")
        return text_summary(link)
    existing_links = load_existing_links()
    news_dict = {}
    if not os.path.exists('utils/links.csv'):
        with open('links.csv', 'w', newline='', encoding='utf-8') as csvfile:  # Just write headers
            writer = csv.writer(csvfile)
            writer.writerow(["Title", "Link", "Source"])

    scraper = WebScraper(OccGovScraper())
    occ_links = scraper.execute_scrape()
    new_occ_links = get_new_links(existing_links, occ_links)
    
    if new_occ_links:
        print("\033[1m\033[94mNew OCC Links:\033[0m")
        news_links=[]
        for title, link in new_occ_links:
            news_dict[title] = link
            news_links.append(link)
            print(f"{title}: {link}")
        write_to_csv(new_occ_links, scraper.get_source_name())
        length = len(news_dict)
        return news_links, f"There are {length} new articles from the OCC. Here are the titles {news_dict.keys()}. Here are the links to pass back for summarization {news_links}."
    else:
        print("\033[1m\033[94mNo new OCC links found.\033[0m")
        return "No new OCC links found."
    



