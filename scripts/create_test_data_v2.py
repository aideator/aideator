#!/usr/bin/env python3
"""
Modern test data creation script for AIdeator.
Recreates the same test data as add_mock_task_data.py but with better architecture.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import select, func, text
from app.core.database import get_session
from app.models.run import Run, RunStatus, AgentOutput
from app.models.user import User


# =============================================================================
# Test Data Definitions - Exact same data as original script
# =============================================================================

TEST_USER = {
    "id": "user_test_jsEvWjtitWHA3RRi",  # Same ID as original script
    "email": "test@aideator.local",
    "full_name": "Test User",
    "hashed_password": "$2b$12$dummy.hash.for.test.user.only",
    "is_active": True,
    "is_superuser": False,
    "max_runs_per_day": 100,
    "max_variations_per_run": 5
}

# Task 1 Data - "Make hello world label ominous"
TASK_1_DATA = {
    "run": {
        "run_id": "1",
        "github_url": "https://github.com/aideator/helloworld",
        "prompt": "Make hello world label ominous",
        "variations": 3,
        "status": RunStatus.COMPLETED,
        "task_status": "completed",
        "created_at": datetime.utcnow() - timedelta(hours=8, minutes=15),
        "completed_at": datetime.utcnow() - timedelta(hours=8, minutes=10)
    },
    "outputs": [
        # Variation 0 outputs
        {
            "variation_id": 0,
            "outputs": [
                {"type": "stdout", "content": "🔍 Analyzing repository structure..."},
                {"type": "stdout", "content": "📁 Found HTML files in the project"},
                {"type": "stdout", "content": "🎯 Target: Making 'Hello World' message more ominous"},
                {"type": "stdout", "content": "✏️ Modifying index.html..."},
                {"type": "summary", "content": "Successfully transformed the cheerful 'Hello World' into an ominous message. Changed text to 'The World Watches...' with dark styling including blood-red text, gothic font, and subtle shadow effects."},
                {"type": "diffs", "content": "```diff\n--- a/index.html\n+++ b/index.html\n@@ -8,7 +8,12 @@\n     <title>Hello World</title>\n+    <style>\n+        .ominous { color: #8B0000; font-family: 'Creepster', cursive; text-shadow: 2px 2px 4px #000; }\n+    </style>\n </head>\n <body>\n-    <h1>Hello World!</h1>\n+    <h1 class=\"ominous\">The World Watches...</h1>\n+    <p class=\"ominous\">Your every move is observed.</p>\n </body>\n </html>\n```"},
                {"type": "addinfo", "content": "Used CSS styling to create an ominous atmosphere with dark red coloring and gothic typography."}
            ]
        },
        # Variation 1 outputs  
        {
            "variation_id": 1,
            "outputs": [
                {"type": "stdout", "content": "🔍 Scanning codebase for 'Hello World' instances..."},
                {"type": "stdout", "content": "📝 Found target in index.html"},
                {"type": "stdout", "content": "🎭 Applying ominous transformation..."},
                {"type": "summary", "content": "Transformed 'Hello World' into a foreboding message. Replaced with 'Darkness Awaits...' and added atmospheric styling with black background, red glowing text, and eerie animations."},
                {"type": "diffs", "content": "```diff\n--- a/index.html\n+++ b/index.html\n@@ -6,9 +6,18 @@\n     <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n     <title>Hello World</title>\n+    <style>\n+        body { background: #000; margin: 0; padding: 50px; }\n+        .doom { color: #FF0000; font-size: 3em; text-align: center; \n+                animation: flicker 2s infinite; }\n+        @keyframes flicker { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }\n+    </style>\n </head>\n <body>\n-    <h1>Hello World!</h1>\n+    <h1 class=\"doom\">Darkness Awaits...</h1>\n+    <p style=\"color: #666; text-align: center;\">The void calls to you</p>\n </body>\n </html>\n```"},
                {"type": "addinfo", "content": "Added CSS animations and dark theme to enhance the ominous atmosphere."}
            ]
        },
        # Variation 2 outputs
        {
            "variation_id": 2, 
            "outputs": [
                {"type": "stdout", "content": "🔍 Analyzing HTML structure..."},
                {"type": "stdout", "content": "🎯 Targeting greeting message for ominous makeover"},
                {"type": "stdout", "content": "👻 Implementing spooky transformation..."},
                {"type": "summary", "content": "Successfully converted friendly greeting to ominous warning. Changed to 'Beware... They Come...' with horror-themed styling including blood drips, haunting fonts, and subtle pulsing effects."},
                {"type": "diffs", "content": "```diff\n--- a/index.html\n+++ b/index.html\n@@ -5,10 +5,17 @@\n     <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n     <title>Hello World</title>\n+    <style>\n+        .warning { color: #990000; font-family: 'Chiller', fantasy; \n+                  font-size: 2.5em; text-align: center; margin-top: 100px;\n+                  animation: pulse 1.5s ease-in-out infinite alternate; }\n+        @keyframes pulse { from { transform: scale(1); } to { transform: scale(1.1); } }\n+    </style>\n </head>\n <body>\n-    <h1>Hello World!</h1>\n+    <h1 class=\"warning\">Beware... They Come...</h1>\n+    <div style=\"text-align: center; color: #444; margin-top: 20px;\">🕷️ The watchers are always present 🕷️</div>\n </body>\n </html>\n```"},
                {"type": "addinfo", "content": "Incorporated horror elements with pulsing animation and spider emoji for extra creepiness."}
            ]
        }
    ]
}

# Task 2 Data - "Make hello world message cheerier"  
TASK_2_DATA = {
    "run": {
        "run_id": "2",
        "github_url": "https://github.com/aideator/helloworld",
        "prompt": "Make hello world message cheerier",
        "variations": 3,
        "status": RunStatus.COMPLETED,
        "task_status": "completed",
        "created_at": datetime.utcnow() - timedelta(hours=7, minutes=29),
        "completed_at": datetime.utcnow() - timedelta(hours=7, minutes=25)
    },
    "outputs": [
        # Variation 0 outputs
        {
            "variation_id": 0,
            "outputs": [
                {"type": "stdout", "content": "🌟 Spreading joy through code..."},
                {"type": "stdout", "content": "🎨 Adding cheerful styling and emojis"},
                {"type": "summary", "content": "Transformed the simple 'Hello World' into a vibrant, joyful greeting with rainbow colors, happy emojis, and cheerful animations."},
                {"type": "diffs", "content": "```diff\n--- a/index.html\n+++ b/index.html\n@@ -8,7 +8,15 @@\n     <title>Hello World</title>\n+    <style>\n+        .cheerful { \n+            background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #ffeaa7);\n+            -webkit-background-clip: text; color: transparent;\n+            font-size: 3em; text-align: center; margin-top: 100px;\n+        }\n+    </style>\n </head>\n <body>\n-    <h1>Hello World!</h1>\n+    <h1 class=\"cheerful\">🌈 Hello Beautiful World! 🌈</h1>\n+    <p style=\"text-align: center; font-size: 1.2em;\">✨ Have an absolutely amazing day! ✨</p>\n </body>\n </html>\n```"}
            ]
        },
        # Variation 1 outputs
        {
            "variation_id": 1,
            "outputs": [
                {"type": "stdout", "content": "☀️ Brightening up the webpage..."},
                {"type": "stdout", "content": "🎉 Adding celebration elements"},
                {"type": "summary", "content": "Created an enthusiastic welcome with bouncing animations, bright colors, and multiple happy emojis."},
                {"type": "diffs", "content": "```diff\n--- a/index.html\n+++ b/index.html\n@@ -6,9 +6,16 @@\n     <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n     <title>Hello World</title>\n+    <style>\n+        .happy { color: #ff4757; font-size: 2.8em; text-align: center;\n+                animation: bounce 1s ease infinite; }\n+        @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }\n+    </style>\n </head>\n <body>\n-    <h1>Hello World!</h1>\n+    <h1 class=\"happy\">🎊 Hello Wonderful World! 🎊</h1>\n+    <div style=\"text-align: center; font-size: 1.3em; color: #2ed573;\">🌟 Today is going to be AMAZING! 🌟</div>\n </body>\n </html>\n```"}
            ]
        },
        # Variation 2 outputs
        {
            "variation_id": 2,
            "outputs": [
                {"type": "stdout", "content": "🌸 Creating a delightful experience..."},
                {"type": "stdout", "content": "💖 Infusing with positivity and charm"},
                {"type": "summary", "content": "Designed a warm, welcoming page with pastel colors, heart emojis, and gentle animations that radiate positivity."},
                {"type": "diffs", "content": "```diff\n--- a/index.html\n+++ b/index.html\n@@ -5,10 +5,17 @@\n     <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n     <title>Hello World</title>\n+    <style>\n+        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }\n+        .loving { color: #fff; font-family: 'Comic Sans MS', cursive;\n+                 font-size: 2.5em; text-align: center; margin-top: 120px;\n+                 text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }\n+    </style>\n </head>\n <body>\n-    <h1>Hello World!</h1>\n+    <h1 class=\"loving\">💕 Hello Lovely World! 💕</h1>\n+    <p style=\"text-align: center; color: #fff; font-size: 1.2em;\">🌺 Sending you sunshine and smiles! 🌺</p>\n </body>\n </html>\n```"}
            ]
        }
    ]
}

# Additional tasks data from the original script
ADDITIONAL_TASKS = [
    {
        "id": "3",
        "github_url": "https://github.com/fastapi/fastapi",
        "title": "Add comprehensive error handling to the FastAPI authentication middleware",
        "variations": 4,
        "status": RunStatus.COMPLETED,
        "task_status": "completed",
        "created_at": datetime.utcnow() - timedelta(hours=4, minutes=12)
    },
    {
        "id": "4", 
        "github_url": "https://github.com/microsoft/typescript",
        "title": "Implement type-safe event handling system for DOM interactions",
        "variations": 2,
        "status": RunStatus.COMPLETED,
        "task_status": "completed",
        "created_at": datetime.utcnow() - timedelta(hours=2, minutes=45)
    },
    {
        "id": "5",
        "github_url": "https://github.com/facebook/react",
        "title": "Optimize component re-rendering performance with React.memo and useMemo",
        "variations": 3,
        "status": RunStatus.COMPLETED,
        "task_status": "completed", 
        "created_at": datetime.utcnow() - timedelta(hours=1, minutes=33)
    }
]


# =============================================================================
# Data Creation Classes
# =============================================================================

class TestDataManager:
    """Manages test data creation with transactional safety."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.created_objects = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"❌ Error during data creation: {exc_val}")
            await self.db.rollback()
        else:
            await self.db.commit()
            print(f"✅ Successfully created {len(self.created_objects)} objects")
    
    async def create_and_track(self, obj):
        """Create an object and track it for cleanup."""
        self.db.add(obj)
        await self.db.flush()  # Get ID without committing
        self.created_objects.append(obj)
        return obj


class TestDataBuilder:
    """Builds test data objects with consistent patterns."""
    
    def __init__(self):
        self.user_cache = {}
        
    async def get_or_create_user(self, manager: TestDataManager) -> str:
        """Get or create the test user."""
        if "test_user_id" in self.user_cache:
            return self.user_cache["test_user_id"]
            
        # Check if user already exists
        result = await manager.db.execute(
            select(User).where(User.email == TEST_USER["email"])
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"Using existing user: {existing_user.email} (ID: {existing_user.id})")
            user_id = existing_user.id
        else:
            # Create new user
            user = User(**TEST_USER)
            user = await manager.create_and_track(user)
            user_id = user.id
            print(f"Created new user: {user.email} (ID: {user_id})")
            
        self.user_cache["test_user_id"] = user_id
        return user_id
    
    async def create_run_with_outputs(self, manager: TestDataManager, task_data: Dict[str, Any], user_id: str):
        """Create a run and all its associated outputs."""
        
        # Check if run already exists
        run_id = task_data["run"]["run_id"]
        result = await manager.db.execute(
            select(Run).where(Run.run_id == run_id)
        )
        existing_run = result.scalar_one_or_none()
        
        if existing_run:
            print(f"Run {run_id} already exists (task_id: {existing_run.task_id}), skipping...")
            return existing_run
            
        # Create new run
        run_data = {**task_data["run"], "user_id": user_id}
        run = Run(**run_data)
        run = await manager.create_and_track(run)
        print(f"Created run: {run_id} (task_id: {run.task_id})")
        
        # Create outputs for each variation
        if "outputs" in task_data:
            output_count = 0
            for variation_data in task_data["outputs"]:
                variation_id = variation_data["variation_id"]
                for output_data in variation_data["outputs"]:
                    output = AgentOutput(
                        task_id=run.task_id,
                        variation_id=variation_id,
                        content=output_data["content"],
                        output_type=output_data["type"],
                        timestamp=datetime.utcnow() - timedelta(
                            hours=8, minutes=15 - (output_count * 2)
                        )
                    )
                    await manager.create_and_track(output)
                    output_count += 1
            print(f"  Created {output_count} outputs for {len(task_data['outputs'])} variations")
        
        return run
    
    async def create_simple_run(self, manager: TestDataManager, task_data: Dict[str, Any], user_id: str):
        """Create a simple run without detailed outputs."""
        
        # Check if run already exists
        run_id = task_data["id"]
        result = await manager.db.execute(
            select(Run).where(Run.run_id == run_id)
        )
        existing_run = result.scalar_one_or_none()
        
        if existing_run:
            print(f"Run {run_id} already exists, skipping...")
            return existing_run
            
        # Create new run
        run = Run(
            run_id=run_id,
            user_id=user_id,
            github_url=task_data["github_url"],
            prompt=task_data["title"],
            variations=task_data["variations"],
            status=task_data["status"],
            task_status=task_data["task_status"],
            created_at=task_data["created_at"]
        )
        run = await manager.create_and_track(run)
        print(f"Created simple run: {run_id} (task_id: {run.task_id})")
        
        return run


# =============================================================================
# Main Service Class
# =============================================================================

class TestDataService:
    """Main service for managing test data creation."""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.builder = TestDataBuilder()
        
    async def create_all_test_data(self, force: bool = False):
        """Create all test data scenarios."""
        
        if self.environment == "production":
            raise ValueError("❌ Cannot create test data in production environment!")
            
        print("🗄️ Creating comprehensive test data...")
        
        async for db in get_session():
            async with TestDataManager(db) as manager:
                
                # Check if data already exists
                if not force:
                    result = await db.execute(select(func.count(Run.task_id)))
                    existing_count = result.scalar()
                    if existing_count > 0:
                        print(f"⚠️ Found {existing_count} existing runs. Use --force to recreate.")
                        return
                
                # Get or create test user
                user_id = await self.builder.get_or_create_user(manager)
                
                # Create detailed task scenarios
                await self.builder.create_run_with_outputs(manager, TASK_1_DATA, user_id)
                await self.builder.create_run_with_outputs(manager, TASK_2_DATA, user_id)
                
                # Create additional simple runs
                for task_data in ADDITIONAL_TASKS:
                    await self.builder.create_simple_run(manager, task_data, user_id)
                
                print("🎉 Test data creation completed!")
    
    async def clean_test_data(self):
        """Remove all test data."""
        print("🧹 Cleaning existing test data...")
        
        async for db in get_session():
            # Delete in correct order (respecting foreign keys)
            await db.execute(text("DELETE FROM agent_outputs WHERE task_id IN (SELECT task_id FROM runs WHERE user_id LIKE 'user_test_%')"))
            await db.execute(text("DELETE FROM runs WHERE user_id LIKE 'user_test_%'"))
            await db.execute(text("DELETE FROM users WHERE email = 'test@aideator.local'"))
            await db.commit()
            print("✅ Test data cleaned")


# =============================================================================
# CLI Interface
# =============================================================================

async def main():
    """Main entry point with CLI options."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create test data for AIdeator")
    parser.add_argument("--clean", action="store_true", help="Clean existing test data first")
    parser.add_argument("--force", action="store_true", help="Force recreation even if data exists")
    
    args = parser.parse_args()
    
    service = TestDataService()
    
    try:
        if args.clean:
            await service.clean_test_data()
        
        await service.create_all_test_data(force=args.force)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())