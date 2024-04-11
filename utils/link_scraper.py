import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
import logging
import os
import csv
import smtplib
from email.message import EmailMessage

#############################################
### Single Link Scraper
#############################################

def text_summary(link: str) -> str:
    """Extract text from a single link."""
    url = link
    # Send a GET request to the website
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the content of the page
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the section with the specified class
        content_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])
        # Check if the section is found
        extracted_text = ' '.join(element.get_text(strip=True) for element in content_elements)
        return extracted_text
    else:
        return f"Failed to retrieve the webpage. Status code: {response.status_code}"