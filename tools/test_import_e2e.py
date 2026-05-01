"""Integration test for import feature through command flow."""

import asyncio
import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.commands.setup import get_command_registry
from app.application.services.command_dispatcher import CommandDispatcher
from app.infrastructure.database import get_session_maker


async def test_import_flow():
    """
    End-to-end test: User sends /import command through entire flow.
    
    Flow:
    1. User sends: /import https://www.facebook.com/share/p/1DJys3DVKH/
    2. CommandParser parses command
    3. CommandDispatcher routes to handle_import
    4. handle_import calls ImportSourceUseCase
    5. ImportSourceUseCase saves to both layers
    6. Response is returned
    """
    print("\n" + "="*60)
    print("IMPORT FEATURE END-TO-END TEST")
    print("="*60)
    
    # Get registry and dispatcher
    registry = get_command_registry()
    dispatcher = CommandDispatcher(registry)
    
    # Test data
    facebook_url = "https://www.facebook.com/share/p/1DJys3DVKH/"
    chat_id = "test_chat_123"
    user_id = "test_user_john"
    
    print(f"\n📱 Simulating user message:")
    print(f"   Command: /import {facebook_url}")
    print(f"   User ID: {user_id}")
    
    # Dispatch command
    print(f"\n🔄 Processing command...")
    command, response = await dispatcher.dispatch(
        "import",
        {"query": facebook_url},
        user_id
    )
    
    print(f"\n✅ Response received:")
    print(f"   {response}")
    
    # Verify response
    if "successfully" in response.lower():
        print(f"\n✨ Success! Source was imported with:")
        
        # Extract ID from response
        lines = response.split("\n")
        for line in lines:
            if "ID:" in line:
                source_id = line.split(":")[-1].strip()
                print(f"   - Source ID: {source_id}")
            elif "Platform:" in line:
                platform = line.split(":")[-1].strip()
                print(f"   - Platform: {platform}")
            elif "File:" in line:
                file_path = line.split(":")[-1].strip()
                print(f"   - File path: {file_path}")
        
        # Check if file exists
        if Path(file_path).exists():
            print(f"\n📄 Markdown file verification:")
            print(f"   ✅ File exists: {file_path}")
            
            content = Path(file_path).read_text()
            if facebook_url in content:
                print(f"   ✅ File contains URL")
            if "facebook" in content.lower():
                print(f"   ✅ File contains platform info")
        
        # Check database
        print(f"\n💾 Database verification:")
        session_factory = get_session_maker()
        async with session_factory() as session:
            from app.infrastructure.database.models import NodeRecord
            from sqlalchemy import select
            
            result = await session.execute(
                select(NodeRecord).where(NodeRecord.id == source_id)
            )
            node = result.scalar_one_or_none()
            
            if node:
                print(f"   ✅ Node found in database")
                print(f"      - Type: {node.type}")
                print(f"      - Title: {node.title}")
                print(f"      - Status: {node.status}")
                print(f"      - File: {node.file_path}")
            else:
                print(f"   ❌ Node not found in database")
    else:
        print(f"\n❌ Import failed!")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n🚀 Starting import feature end-to-end test...\n")
    asyncio.run(test_import_flow())
