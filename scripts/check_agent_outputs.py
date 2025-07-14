#!/usr/bin/env python3
"""Check agent_outputs table for persisted data."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, create_engine, func, select

from app.models.run import AgentOutput

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not set")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

# Create session
with Session(engine) as session:
    # Get total count
    total_count = session.exec(select(func.count(AgentOutput.id))).one()
    print(f"📊 Total rows in agent_outputs: {total_count}")

    # Get output type distribution
    print("\n📈 Output types distribution:")
    result = session.exec(
        select(AgentOutput.output_type, func.count(AgentOutput.id))
        .group_by(AgentOutput.output_type)
        .order_by(func.count(AgentOutput.id).desc())
    )
    for output_type, count in result:
        print(f"  {output_type}: {count}")

    # Get recent outputs
    print("\n📝 Most recent 10 outputs:")
    recent_outputs = session.exec(
        select(AgentOutput).order_by(AgentOutput.timestamp.desc()).limit(10)
    ).all()

    for output in recent_outputs:
        content_preview = output.content[:80] if output.content else "None"
        print(f"\n  Run: {output.run_id[:8]}..., Var: {output.variation_id}")
        print(f"  Type: {output.output_type}, Time: {output.timestamp}")
        print(f"  Content: {content_preview}...")

    # Check for specific run if provided
    if len(sys.argv) > 1:
        run_id = sys.argv[1]
        print(f"\n🔍 Outputs for run {run_id}:")
        run_outputs = session.exec(
            select(AgentOutput)
            .where(AgentOutput.run_id == run_id)
            .order_by(AgentOutput.timestamp)
        ).all()

        if run_outputs:
            for output in run_outputs:
                print(
                    f"\n  [{output.timestamp}] Var {output.variation_id} - {output.output_type}"
                )
                print(f"  {output.content[:200]}...")
        else:
            print("  No outputs found for this run")
