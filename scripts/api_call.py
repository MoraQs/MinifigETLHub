# # # retrieve API details
# def ingest_api_data():
#     """Ingesting data from Rebrickable REST API"""

#     api_url = os.getenv('API_URL')
#     api_key = os.getenv('API_KEY')
    
#     # Define headers with API key
#     headers = {
#         "Authorization": f"key {api_key}"
#     }
    
#     all_data = []  # List to store all records
#     next_page_url = api_url  # Start with the initial API URL
#     delay_time = 1  # Set delay time (in seconds)
    
#     while next_page_url:
#         response = requests.get(next_page_url, headers=headers)
        
#         if response.status_code == 200:
#             data = response.json()  # Convert API response to JSON
            
#             # Append records to all_data list
#             if "results" in data:
#                 all_data.extend(data["results"])  # Add new records
                
#             # Check if there is a next page
#             next_page_url = data.get("next")  # Get next page URL (if available)
            
#             print(f"Fetched {len(all_data)} records so far...")  # Debugging output
    
#             # Add delay before the next request
#             time.sleep(delay_time)
    
#         elif response.status_code == 429:
#             # API rate limit hit: Wait and retry
#             retry_after = int(response.headers.get("Retry-After", delay_time))
#             print(f"Rate limit exceeded! Waiting for {retry_after} seconds before retrying...")
#             time.sleep(retry_after)
            
#         else:
#             print(f"Failed to fetch data: {response.status_code}, {response.text}")
#             break  # Stop if there's an error

#     return pd.DataFrame(all_data)   # Convert list to DataFrame

# df = ingest_api_data()  