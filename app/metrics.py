from prometheus_client import Counter, Histogram

# Cache hit/miss rates
CACHE_REQUESTS = Counter(
    "cache_requests_total", 
    "Total Redis cache requests", 
    ["status"] 
)

# Response times
API_RESPONSE_TIME = Histogram(
    "api_response_time_seconds", 
    "Response time in seconds", 
    ["source"] 
)

# Recipe popularity
RECIPE_SEARCHES = Counter(
    "recipe_searches_total", 
    "Frequency of recipe searches", 
    ["query"] 
)

# External API success/failure
EXTERNAL_API_CALLS = Counter(
    "external_api_calls_total", 
    "External API call status", 
    ["api", "status"] 
)