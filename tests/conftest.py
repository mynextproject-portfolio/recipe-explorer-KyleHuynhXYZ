"""
Test fixtures for Recipe Explorer tests.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.storage import recipe_storage
from app.deps import get_external_client


@pytest.fixture
def client():
    """Test client for making requests to the API"""
    return TestClient(app)


@pytest.fixture
def clean_storage():
    """Reset storage before and after each test"""
    # Clear the SQLite database using the new storage engine's connection
    with recipe_storage._get_connection() as conn:
        conn.execute("DELETE FROM recipes")
        conn.commit()
    
    yield # This allows the test to run
    
    # Run the exact same cleanup after the test finishes
    with recipe_storage._get_connection() as conn:
        conn.execute("DELETE FROM recipes")
        conn.commit()

@pytest.fixture
def sample_recipe_data():
    """Sample recipe for testing"""
    return {
        "title": "Test Recipe",
        "description": "A test recipe",
        "cuisine": "Fusion",
        "ingredients": ["ingredient 1", "ingredient 2"],
        "instructions": ["First, do step 1.", "Then, do step 2."],
        "servings": 2,
        "tags": ["test"],
    }


@pytest.fixture
def mock_external_client():
    """Factory to create a mock external client for dependency override testing"""

    class MockExternalClient:
        """Mock external client that satisfies ExternalClientProtocol"""

        def __init__(self):
            self.cache_hits = 0
            self.cache_misses = 0
            self.search_results = []
            self.meal_result = None

        def search_meals(self, query: str):
            """Return configured search results"""
            return self.search_results

        def get_meal_by_id(self, meal_id: str):
            """Return configured meal result"""
            return self.meal_result

    return MockExternalClient()


@pytest.fixture
def override_external_client(mock_external_client):
    """Override the external client dependency for testing"""
    app.dependency_overrides[get_external_client] = lambda: mock_external_client
    yield mock_external_client
    # Clean up
    del app.dependency_overrides[get_external_client]
