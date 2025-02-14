import os
import requests
from typing import Dict, Any
from config import get_scrapin_random_api_key
from sample_data import data, job_data
from dotenv import load_dotenv
load_dotenv() ## loading all the environment variables


# Scraping API DOCs: https://docs.scrapin.io/quickstart
class ScrapinAPI:
    def __init__(self):
        """
        Initialize the ScrapinAPI client with API key.
        Args:
            api_key (str): API key obtained from the developer dashboard
        """
        self.profile_url = "https://api.scrapin.io/enrichment/profile"
        self.job_url = "https://api.scrapin.io/enrichment/jobs/details"
        self.api_key = get_scrapin_random_api_key()

    # Get Profile Details
    def get_person_profile(self, linkedin_url: str) -> Dict[str, Any]:
        """
        Extract person's profile data from LinkedIn URL.
        Args:
            linkedin_url (str): Valid LinkedIn profile URL in format:
                              https://www.linkedin.com/in/xxxxxxxxxxxxx/
        Returns:
            dict: Response JSON containing profile data
        """
        # Validate URL format
        if not linkedin_url.startswith("https://www.linkedin.com/in/"):
            return {
                    "success": False,
                    "title": "Not Found",
                    "msg": "Invalid LinkedIn URL format. Must start with: https://www.linkedin.com/in/"
                    }
        # Prepare query parameters
        params = {
            "apikey": self.api_key,
            "linkedInUrl": linkedin_url
        }

        # Make API request
        response = requests.get(
            url=self.profile_url,
            params=params,
            headers={"Accept": "application/json"}
        )

        # Check for HTTP errors
        # response.raise_for_status()

        return response.json()
    
    # Get Job Details
    def get_job_details(self, linkedin_job_url: str) -> Dict[str, Any]:
        """
        Extract Job data from LinkedIn Job URL.
        
        Args:
            url (str): Valid LinkedIn URL of the job with the following formats: 
            https://www.linkedin.com/jobs/collections/recommended/?currentJobId=XXXXXXXXXX, 
            https://www.linkedin.com/jobs/search/?currentJobId=XXXXXXXXXX or 
            https://www.linkedin.com/jobs/view/XXXXXXXXXX/.
        
        Returns:
            dict: Response JSON containing job data
        """
        # Validate URL format
        if not linkedin_job_url.startswith("https://www.linkedin.com/jobs/"):
            return {
                    "success": False,
                    "title": "Not Found",
                    "msg": "Invalid LinkedIn URL format. Must start with: https://www.linkedin.com/jobs/"
                    }
        # Prepare query parameters
        params = {
            "apikey": self.api_key,
            "url": linkedin_job_url
        }

        # Make API request
        response = requests.get(
            url=self.job_url,
            params=params,
            headers={"Accept": "application/json"}
        )

        # Check for HTTP errors
        # response.raise_for_status()

        return response.json()


# Function to get data from LinkedIn profile
def get_profile_data(profile_url):
    client = ScrapinAPI()

    # Get profile data
    # profile_url = "https://www.linkedin.com/in/andrewyng/"
    profile_data = client.get_person_profile(profile_url)
    
    return profile_data
    # return data

def get_Job_data(job_url):
    client = ScrapinAPI()

    # Get Job data
    # job_url = "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=3931053459"
    job_data = client.get_job_details(job_url)
    
    return job_data
        


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = ScrapinAPI()

    try:
        # Get profile data
        profile_url = "https://www.linkedin.com/in/anasdasfaefdrewfwesdyng/"
        profile_data = client.get_person_profile(profile_url)
        
        # Print the results
        print("Successfully retrieved profile data:")
        print(profile_data)

    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}")
    except ValueError as e:
        print(f"Validation Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")