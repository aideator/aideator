"""
Integration tests for session and preference APIs.

These tests verify:
1. Session CRUD operations
2. Preference recording and analytics
3. Data persistence and consistency
4. Error handling and validation
5. API security and permissions
"""

import asyncio
import json
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import get_settings

settings = get_settings()
from app.core.database import get_session
from app.models.user import User
from app.models.session import Session, Preference
from app.schemas.session import SessionCreate, SessionUpdate
from app.schemas.preference import PreferenceCreate


class TestSessionAPI:
    """Test suite for Session API endpoints."""
    
    @pytest.fixture(scope="class")
    def test_client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def test_user_id(self):
        """Test user ID for authentication."""
        return str(uuid.uuid4())
    
    @pytest.fixture(scope="class")
    def auth_headers(self, test_user_id):
        """Authentication headers for API requests."""
        return {"Authorization": f"Bearer test-token-{test_user_id}"}
    
    @pytest.fixture(scope="class")
    def sample_sessions(self):
        """Sample session data for testing."""
        return [
            {
                "title": "Test Session 1",
                "expected_turn_count": 3,
                "last_prompt": "What is AI?"
            },
            {
                "title": "Test Session 2",
                "expected_turn_count": 1,
                "last_prompt": "Explain machine learning"
            },
            {
                "title": "Test Session 3",
                "expected_turn_count": 5,
                "last_prompt": "Compare different models"
            }
        ]
    
    def test_create_session(self, test_client, auth_headers):
        """Test creating a new session."""
        # Test with title
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "My New Session"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["title"] == "My New Session"
        assert "created_at" in data
        
        # Test without title (should get auto-generated)
        response = test_client.post(
            "/api/v1/sessions",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["title"].startswith("Session")  # Auto-generated title
        
        return data["session_id"]
    
    def test_get_sessions(self, test_client, auth_headers, sample_sessions):
        """Test retrieving user sessions."""
        # Create test sessions
        session_ids = []
        for session_data in sample_sessions:
            response = test_client.post(
                "/api/v1/sessions",
                json={"title": session_data["title"]},
                headers=auth_headers
            )
            assert response.status_code == 200
            session_ids.append(response.json()["session_id"])
        
        # Get all sessions
        response = test_client.get("/api/v1/sessions", headers=auth_headers)
        
        assert response.status_code == 200
        sessions = response.json()
        assert len(sessions) >= len(sample_sessions)
        
        # Verify session structure
        for session in sessions:
            assert "session_id" in session
            assert "title" in session
            assert "created_at" in session
            assert "updated_at" in session
            assert "turn_count" in session
            assert isinstance(session["turn_count"], int)
        
        # Test pagination
        response = test_client.get(
            "/api/v1/sessions?limit=2&offset=0",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        limited_sessions = response.json()
        assert len(limited_sessions) <= 2
        
        return session_ids
    
    def test_get_session_details(self, test_client, auth_headers):
        """Test retrieving detailed session information."""
        # Create test session
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Detailed Session"},
            headers=auth_headers
        )
        session_id = response.json()["session_id"]
        
        # Get session details
        response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        session_details = response.json()
        
        # Verify structure
        assert session_details["session_id"] == session_id
        assert session_details["title"] == "Detailed Session"
        assert "turns" in session_details
        assert isinstance(session_details["turns"], list)
        assert session_details["turn_count"] == 0  # New session has no turns
        
        # Test non-existent session
        fake_session_id = str(uuid.uuid4())
        response = test_client.get(
            f"/api/v1/sessions/{fake_session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_update_session(self, test_client, auth_headers):
        """Test updating session title."""
        # Create test session
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Original Title"},
            headers=auth_headers
        )
        session_id = response.json()["session_id"]
        
        # Update session title
        response = test_client.put(
            f"/api/v1/sessions/{session_id}",
            json={"title": "Updated Title"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify update
        response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        session_details = response.json()
        assert session_details["title"] == "Updated Title"
        
        # Test invalid update
        response = test_client.put(
            f"/api/v1/sessions/{session_id}",
            json={"title": ""},  # Empty title
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_delete_session(self, test_client, auth_headers):
        """Test deleting a session."""
        # Create test session
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Session to Delete"},
            headers=auth_headers
        )
        session_id = response.json()["session_id"]
        
        # Delete session
        response = test_client.delete(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify deletion
        response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        
        # Test deleting non-existent session
        fake_session_id = str(uuid.uuid4())
        response = test_client.delete(
            f"/api/v1/sessions/{fake_session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_session_export(self, test_client, auth_headers):
        """Test session export functionality."""
        # Create test session
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Export Session"},
            headers=auth_headers
        )
        session_id = response.json()["session_id"]
        
        # Test JSON export
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/export?format=json",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        export_data = response.json()
        assert "session_id" in export_data
        assert "title" in export_data
        assert "turns" in export_data
        
        # Test Markdown export
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/export?format=markdown",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "text/markdown" in response.headers["content-type"]
        
        markdown_content = response.text
        assert "# Export Session" in markdown_content
    
    def test_session_permissions(self, test_client):
        """Test session access permissions."""
        # Create session with user 1
        user1_headers = {"Authorization": "Bearer test-token-user1"}
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "User 1 Session"},
            headers=user1_headers
        )
        session_id = response.json()["session_id"]
        
        # Try to access with user 2
        user2_headers = {"Authorization": "Bearer test-token-user2"}
        response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=user2_headers
        )
        
        assert response.status_code == 403  # Forbidden
    
    def test_session_validation(self, test_client, auth_headers):
        """Test session input validation."""
        # Test title too long
        long_title = "A" * 300  # Assuming max length is 255
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": long_title},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        
        # Test invalid session ID format
        response = test_client.get(
            "/api/v1/sessions/invalid-id",
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_session_concurrency(self, test_client, auth_headers):
        """Test concurrent session operations."""
        import threading
        import time
        
        results = []
        
        def create_session(session_num):
            """Create a session in a thread."""
            response = test_client.post(
                "/api/v1/sessions",
                json={"title": f"Concurrent Session {session_num}"},
                headers=auth_headers
            )
            results.append(response.status_code)
        
        # Create multiple sessions concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_session, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all sessions were created successfully
        assert all(status == 200 for status in results)
        assert len(results) == 5


class TestPreferenceAPI:
    """Test suite for Preference API endpoints."""
    
    @pytest.fixture(scope="class")
    def test_client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Authentication headers for API requests."""
        return {"Authorization": "Bearer test-token-preference-user"}
    
    @pytest.fixture(scope="class")
    def sample_preferences(self):
        """Sample preference data for testing."""
        return [
            {
                "prompt_id": str(uuid.uuid4()),
                "chosen_model_id": "gpt-4o-mini",
                "feedback_text": "GPT-4 gave the most accurate answer"
            },
            {
                "prompt_id": str(uuid.uuid4()),
                "chosen_model_id": "claude-3-haiku-20240307",
                "feedback_text": "Claude was more creative"
            },
            {
                "prompt_id": str(uuid.uuid4()),
                "chosen_model_id": "gpt-4o-mini",
                "feedback_text": "GPT-4 was faster"
            },
            {
                "prompt_id": str(uuid.uuid4()),
                "chosen_model_id": "gemini-1.5-flash",
                "feedback_text": "Gemini provided better structure"
            },
            {
                "prompt_id": str(uuid.uuid4()),
                "chosen_model_id": "claude-3-haiku-20240307",
                "feedback_text": "Claude understood context better"
            }
        ]
    
    def test_record_preference(self, test_client, auth_headers, sample_preferences):
        """Test recording user preferences."""
        for preference in sample_preferences:
            response = test_client.post(
                "/api/v1/preferences",
                json=preference,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "preference_id" in data
            assert "created_at" in data
        
        # Test without feedback text
        response = test_client.post(
            "/api/v1/preferences",
            json={
                "prompt_id": str(uuid.uuid4()),
                "chosen_model_id": "gpt-4o-mini"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_get_preference_stats(self, test_client, auth_headers, sample_preferences):
        """Test retrieving preference statistics."""
        # Record preferences first
        for preference in sample_preferences:
            test_client.post(
                "/api/v1/preferences",
                json=preference,
                headers=auth_headers
            )
        
        # Get preference statistics
        response = test_client.get("/api/v1/preferences/stats", headers=auth_headers)
        
        assert response.status_code == 200
        stats = response.json()
        
        # Verify structure
        assert "total_preferences" in stats
        assert "model_win_rates" in stats
        assert "favorite_model" in stats
        assert "preference_trends" in stats
        
        # Verify data
        assert stats["total_preferences"] >= len(sample_preferences)
        assert isinstance(stats["model_win_rates"], dict)
        assert isinstance(stats["preference_trends"], list)
        
        # Verify model win rates
        win_rates = stats["model_win_rates"]
        assert all(0 <= rate <= 1 for rate in win_rates.values())
        
        # Verify favorite model is the one with highest win rate
        if win_rates:
            favorite = max(win_rates, key=win_rates.get)
            assert stats["favorite_model"] == favorite
    
    def test_preference_validation(self, test_client, auth_headers):
        """Test preference input validation."""
        # Test invalid prompt ID
        response = test_client.post(
            "/api/v1/preferences",
            json={
                "prompt_id": "invalid-id",
                "chosen_model_id": "gpt-4o-mini"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        
        # Test missing required fields
        response = test_client.post(
            "/api/v1/preferences",
            json={"prompt_id": str(uuid.uuid4())},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        
        # Test empty model ID
        response = test_client.post(
            "/api/v1/preferences",
            json={
                "prompt_id": str(uuid.uuid4()),
                "chosen_model_id": ""
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_preference_duplicate_handling(self, test_client, auth_headers):
        """Test handling of duplicate preferences."""
        prompt_id = str(uuid.uuid4())
        
        # Record first preference
        response = test_client.post(
            "/api/v1/preferences",
            json={
                "prompt_id": prompt_id,
                "chosen_model_id": "gpt-4o-mini",
                "feedback_text": "First choice"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Try to record duplicate (should update existing)
        response = test_client.post(
            "/api/v1/preferences",
            json={
                "prompt_id": prompt_id,
                "chosen_model_id": "claude-3-haiku-20240307",
                "feedback_text": "Changed my mind"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify the preference was updated
        response = test_client.get("/api/v1/preferences/stats", headers=auth_headers)
        stats = response.json()
        
        # Should only count once towards total
        assert stats["total_preferences"] >= 1
    
    def test_preference_analytics(self, test_client, auth_headers):
        """Test preference analytics endpoints."""
        # Create diverse preferences over time
        models = ["gpt-4o-mini", "claude-3-haiku-20240307", "gemini-1.5-flash"]
        
        for i, model in enumerate(models):
            for j in range(3):  # 3 preferences per model
                response = test_client.post(
                    "/api/v1/preferences",
                    json={
                        "prompt_id": str(uuid.uuid4()),
                        "chosen_model_id": model,
                        "feedback_text": f"Preference {i}-{j}"
                    },
                    headers=auth_headers
                )
                assert response.status_code == 200
        
        # Get analytics
        response = test_client.get("/api/v1/preferences/analytics", headers=auth_headers)
        
        assert response.status_code == 200
        analytics = response.json()
        
        # Verify analytics structure
        assert "model_performance" in analytics
        assert "feedback_analysis" in analytics
        assert "temporal_trends" in analytics
        
        # Verify model performance data
        performance = analytics["model_performance"]
        assert all(model in performance for model in models)
        
        # Verify feedback analysis
        feedback = analytics["feedback_analysis"]
        assert "common_themes" in feedback
        assert "sentiment_distribution" in feedback
    
    def test_preference_export(self, test_client, auth_headers):
        """Test preference data export."""
        # Create test preferences
        for i in range(5):
            test_client.post(
                "/api/v1/preferences",
                json={
                    "prompt_id": str(uuid.uuid4()),
                    "chosen_model_id": "gpt-4o-mini",
                    "feedback_text": f"Test feedback {i}"
                },
                headers=auth_headers
            )
        
        # Test CSV export
        response = test_client.get(
            "/api/v1/preferences/export?format=csv",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        
        csv_content = response.text
        assert "prompt_id,chosen_model_id,feedback_text" in csv_content
        
        # Test JSON export
        response = test_client.get(
            "/api/v1/preferences/export?format=json",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        json_data = response.json()
        assert "preferences" in json_data
        assert isinstance(json_data["preferences"], list)
    
    def test_preference_filtering(self, test_client, auth_headers):
        """Test preference filtering and querying."""
        # Create preferences with specific models
        models = ["gpt-4o-mini", "claude-3-haiku-20240307"]
        
        for model in models:
            for i in range(3):
                test_client.post(
                    "/api/v1/preferences",
                    json={
                        "prompt_id": str(uuid.uuid4()),
                        "chosen_model_id": model,
                        "feedback_text": f"Feedback for {model}"
                    },
                    headers=auth_headers
                )
        
        # Test filtering by model
        response = test_client.get(
            "/api/v1/preferences?model_id=gpt-4o-mini",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        preferences = response.json()
        
        # Verify all results are for the requested model
        assert all(p["chosen_model_id"] == "gpt-4o-mini" for p in preferences)
        
        # Test date range filtering
        from datetime import datetime, timedelta
        
        start_date = (datetime.now() - timedelta(days=1)).isoformat()
        end_date = datetime.now().isoformat()
        
        response = test_client.get(
            f"/api/v1/preferences?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        preferences = response.json()
        
        # Verify all results are within date range
        for pref in preferences:
            pref_date = datetime.fromisoformat(pref["created_at"].replace("Z", "+00:00"))
            assert start_date <= pref_date.isoformat() <= end_date


class TestSessionPreferenceIntegration:
    """Test suite for session-preference integration."""
    
    @pytest.fixture(scope="class")
    def test_client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Authentication headers for API requests."""
        return {"Authorization": "Bearer test-token-integration"}
    
    def test_session_with_preferences(self, test_client, auth_headers):
        """Test session lifecycle with preferences."""
        # Create session
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Session with Preferences"},
            headers=auth_headers
        )
        session_id = response.json()["session_id"]
        
        # Create prompts in session
        prompt_ids = []
        for i in range(3):
            response = test_client.post(
                "/api/v1/prompts",
                json={
                    "prompt": f"Test prompt {i}",
                    "models": ["gpt-4o-mini", "claude-3-haiku-20240307"],
                    "session_id": session_id
                },
                headers=auth_headers
            )
            prompt_ids.append(response.json()["prompt_id"])
        
        # Record preferences for each prompt
        for i, prompt_id in enumerate(prompt_ids):
            chosen_model = "gpt-4o-mini" if i % 2 == 0 else "claude-3-haiku-20240307"
            response = test_client.post(
                "/api/v1/preferences",
                json={
                    "prompt_id": prompt_id,
                    "chosen_model_id": chosen_model,
                    "feedback_text": f"Preference {i}"
                },
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Get session details with preferences
        response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        session_details = response.json()
        
        # Verify session has turns with preferences
        assert len(session_details["turns"]) == 3
        
        for turn in session_details["turns"]:
            assert "selected_model_id" in turn
            assert turn["selected_model_id"] is not None
    
    def test_session_analytics_with_preferences(self, test_client, auth_headers):
        """Test session analytics including preference data."""
        # Create session with multiple turns and preferences
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Analytics Session"},
            headers=auth_headers
        )
        session_id = response.json()["session_id"]
        
        # Create multiple prompts with different model preferences
        models = ["gpt-4o-mini", "claude-3-haiku-20240307", "gemini-1.5-flash"]
        
        for i in range(6):
            # Create prompt
            response = test_client.post(
                "/api/v1/prompts",
                json={
                    "prompt": f"Analytics prompt {i}",
                    "models": models,
                    "session_id": session_id
                },
                headers=auth_headers
            )
            prompt_id = response.json()["prompt_id"]
            
            # Record preference (rotate through models)
            chosen_model = models[i % len(models)]
            test_client.post(
                "/api/v1/preferences",
                json={
                    "prompt_id": prompt_id,
                    "chosen_model_id": chosen_model,
                    "feedback_text": f"Analytics feedback {i}"
                },
                headers=auth_headers
            )
        
        # Get session analytics
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        analytics = response.json()
        
        # Verify analytics structure
        assert "model_preferences" in analytics
        assert "session_summary" in analytics
        assert "turn_analysis" in analytics
        
        # Verify model preferences
        model_prefs = analytics["model_preferences"]
        assert all(model in model_prefs for model in models)
        
        # Verify session summary
        summary = analytics["session_summary"]
        assert summary["total_turns"] == 6
        assert summary["models_used"] == len(models)
    
    def test_preference_impact_on_session_recommendations(self, test_client, auth_headers):
        """Test how preferences affect session recommendations."""
        # Create session
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Recommendation Session"},
            headers=auth_headers
        )
        session_id = response.json()["session_id"]
        
        # Create strong preference pattern (favor GPT-4)
        for i in range(10):
            # Create prompt
            response = test_client.post(
                "/api/v1/prompts",
                json={
                    "prompt": f"Recommendation prompt {i}",
                    "models": ["gpt-4o-mini", "claude-3-haiku-20240307"],
                    "session_id": session_id
                },
                headers=auth_headers
            )
            prompt_id = response.json()["prompt_id"]
            
            # Always prefer GPT-4
            test_client.post(
                "/api/v1/preferences",
                json={
                    "prompt_id": prompt_id,
                    "chosen_model_id": "gpt-4o-mini",
                    "feedback_text": "GPT-4 is better"
                },
                headers=auth_headers
            )
        
        # Get recommendations for new prompt
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/recommendations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        recommendations = response.json()
        
        # Verify GPT-4 is recommended first
        assert "recommended_models" in recommendations
        recommended_models = recommendations["recommended_models"]
        assert recommended_models[0]["model_id"] == "gpt-4o-mini"
        assert recommended_models[0]["confidence"] > 0.8
    
    def test_session_preference_consistency(self, test_client, auth_headers):
        """Test consistency between session and preference data."""
        # Create session
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Consistency Test"},
            headers=auth_headers
        )
        session_id = response.json()["session_id"]
        
        # Create prompt and preference
        response = test_client.post(
            "/api/v1/prompts",
            json={
                "prompt": "Consistency test prompt",
                "models": ["gpt-4o-mini", "claude-3-haiku-20240307"],
                "session_id": session_id
            },
            headers=auth_headers
        )
        prompt_id = response.json()["prompt_id"]
        
        # Record preference
        test_client.post(
            "/api/v1/preferences",
            json={
                "prompt_id": prompt_id,
                "chosen_model_id": "gpt-4o-mini",
                "feedback_text": "Consistency test"
            },
            headers=auth_headers
        )
        
        # Get session details
        response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        session_details = response.json()
        
        # Get preference stats
        response = test_client.get("/api/v1/preferences/stats", headers=auth_headers)
        preference_stats = response.json()
        
        # Verify consistency
        turn = session_details["turns"][0]
        assert turn["selected_model_id"] == "gpt-4o-mini"
        assert preference_stats["total_preferences"] >= 1
        assert "gpt-4o-mini" in preference_stats["model_win_rates"]
    
    def test_batch_preference_operations(self, test_client, auth_headers):
        """Test batch operations for preferences."""
        # Create session
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Batch Test Session"},
            headers=auth_headers
        )
        session_id = response.json()["session_id"]
        
        # Create multiple prompts
        prompt_ids = []
        for i in range(5):
            response = test_client.post(
                "/api/v1/prompts",
                json={
                    "prompt": f"Batch prompt {i}",
                    "models": ["gpt-4o-mini", "claude-3-haiku-20240307"],
                    "session_id": session_id
                },
                headers=auth_headers
            )
            prompt_ids.append(response.json()["prompt_id"])
        
        # Batch record preferences
        batch_preferences = [
            {
                "prompt_id": prompt_id,
                "chosen_model_id": "gpt-4o-mini" if i % 2 == 0 else "claude-3-haiku-20240307",
                "feedback_text": f"Batch feedback {i}"
            }
            for i, prompt_id in enumerate(prompt_ids)
        ]
        
        response = test_client.post(
            "/api/v1/preferences/batch",
            json={"preferences": batch_preferences},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["processed"] == len(batch_preferences)
        assert result["errors"] == 0
        
        # Verify all preferences were recorded
        response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        session_details = response.json()
        
        assert len(session_details["turns"]) == 5
        assert all(turn["selected_model_id"] is not None for turn in session_details["turns"])