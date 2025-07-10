from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlmodel import Session as SQLSession

from app.core.database import get_session
from app.core.dependencies import CurrentUser
from app.models.user import User
from app.models.session import Session, Turn, Preference
from app.schemas.session import (
    SessionCreate, SessionUpdate, SessionResponse, SessionListResponse,
    TurnCreate, TurnResponse, PreferenceCreate, PreferenceResponse,
    SessionAnalytics, ModelPerformanceMetrics, SessionExport
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/", response_model=SessionListResponse)
async def get_sessions(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False),
    archived_only: bool = Query(False),
):
    """Get user's sessions with pagination."""
    query = select(Session).where(Session.user_id == current_user.id)
    
    if active_only:
        query = query.where(Session.is_active == True)
    elif archived_only:
        query = query.where(Session.is_archived == True)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get sessions with pagination
    query = query.order_by(desc(Session.last_activity_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return SessionListResponse(
        sessions=sessions,
        total=total,
        limit=limit,
        offset=skip
    )


@router.post("/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session)
):
    """Create a new session."""
    session = Session(
        id=str(uuid4()),
        user_id=current_user.id,
        title=session_data.title,
        description=session_data.description,
        models_used=session_data.models_used
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session)
):
    """Get a specific session."""
    query = select(Session).where(
        and_(Session.id == session_id, Session.user_id == current_user.id)
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_update: SessionUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session)
):
    """Update a session."""
    query = select(Session).where(
        and_(Session.id == session_id, Session.user_id == current_user.id)
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update fields
    update_data = session_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    session.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    
    return session


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session)
):
    """Delete a session."""
    query = select(Session).where(
        and_(Session.id == session_id, Session.user_id == current_user.id)
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.delete(session)
    await db.commit()
    
    return {"message": "Session deleted successfully"}


@router.get("/{session_id}/turns", response_model=List[TurnResponse])
async def get_session_turns(
    session_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session)
):
    """Get all turns for a session."""
    # Verify session ownership
    session_query = select(Session).where(
        and_(Session.id == session_id, Session.user_id == current_user.id)
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get turns
    turns_query = select(Turn).where(Turn.session_id == session_id).order_by(Turn.turn_number)
    turns_result = await db.execute(turns_query)
    turns = turns_result.scalars().all()
    
    return turns


@router.post("/{session_id}/turns", response_model=TurnResponse)
async def create_turn(
    session_id: str,
    turn_data: TurnCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session)
):
    """Create a new turn in a session."""
    # Verify session ownership
    session_query = select(Session).where(
        and_(Session.id == session_id, Session.user_id == current_user.id)
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get next turn number
    turn_count_query = select(func.count(Turn.id)).where(Turn.session_id == session_id)
    turn_count_result = await db.execute(turn_count_query)
    turn_number = turn_count_result.scalar() + 1
    
    # Create turn
    turn = Turn(
        id=str(uuid4()),
        session_id=session_id,
        turn_number=turn_number,
        prompt=turn_data.prompt,
        context=turn_data.context,
        models_requested=turn_data.models_requested
    )
    
    db.add(turn)
    
    # Update session
    session.total_turns += 1
    session.last_activity_at = datetime.utcnow()
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(turn)
    
    return turn


@router.get("/{session_id}/turns/{turn_id}", response_model=TurnResponse)
async def get_turn(
    session_id: str,
    turn_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session)
):
    """Get a specific turn."""
    # Verify session ownership
    session_query = select(Session).where(
        and_(Session.id == session_id, Session.user_id == current_user.id)
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get turn
    turn_query = select(Turn).where(
        and_(Turn.id == turn_id, Turn.session_id == session_id)
    )
    turn_result = await db.execute(turn_query)
    turn = turn_result.scalar_one_or_none()
    
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")
    
    return turn


@router.post("/{session_id}/turns/{turn_id}/preferences", response_model=PreferenceResponse)
async def create_preference(
    session_id: str,
    turn_id: str,
    preference_data: PreferenceCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session)
):
    """Create a preference for a turn."""
    # Verify session ownership
    session_query = select(Session).where(
        and_(Session.id == session_id, Session.user_id == current_user.id)
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify turn exists
    turn_query = select(Turn).where(
        and_(Turn.id == turn_id, Turn.session_id == session_id)
    )
    turn_result = await db.execute(turn_query)
    turn = turn_result.scalar_one_or_none()
    
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")
    
    # Create preference
    preference = Preference(
        id=str(uuid4()),
        user_id=current_user.id,
        session_id=session_id,
        turn_id=turn_id,
        preferred_model=preference_data.preferred_model,
        preferred_response_id=preference_data.preferred_response_id,
        compared_models=preference_data.compared_models,
        response_quality_scores=preference_data.response_quality_scores,
        feedback_text=preference_data.feedback_text,
        confidence_score=preference_data.confidence_score,
        preference_type=preference_data.preference_type
    )
    
    db.add(preference)
    
    # Update session activity
    session.last_activity_at = datetime.utcnow()
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(preference)
    
    return preference


@router.get("/{session_id}/preferences", response_model=List[PreferenceResponse])
async def get_session_preferences(
    session_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session)
):
    """Get all preferences for a session."""
    # Verify session ownership
    session_query = select(Session).where(
        and_(Session.id == session_id, Session.user_id == current_user.id)
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get preferences
    preferences_query = select(Preference).where(
        Preference.session_id == session_id
    ).order_by(Preference.created_at)
    preferences_result = await db.execute(preferences_query)
    preferences = preferences_result.scalars().all()
    
    return preferences


@router.get("/{session_id}/analytics", response_model=SessionAnalytics)
async def get_session_analytics(
    session_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session)
):
    """Get analytics for a specific session."""
    # Verify session ownership
    session_query = select(Session).where(
        and_(Session.id == session_id, Session.user_id == current_user.id)
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get session analytics
    turns_query = select(Turn).where(Turn.session_id == session_id)
    turns_result = await db.execute(turns_query)
    turns = turns_result.scalars().all()
    
    preferences_query = select(Preference).where(Preference.session_id == session_id)
    preferences_result = await db.execute(preferences_query)
    preferences = preferences_result.scalars().all()
    
    # Calculate analytics
    total_cost = sum(turn.total_cost for turn in turns)
    models_used = session.models_used
    
    # Model preference stats
    model_wins = {}
    for pref in preferences:
        model_wins[pref.preferred_model] = model_wins.get(pref.preferred_model, 0) + 1
    
    model_preference_stats = {}
    for model in models_used:
        model_preference_stats[model] = {
            "wins": model_wins.get(model, 0),
            "win_rate": model_wins.get(model, 0) / len(preferences) if preferences else 0
        }
    
    return SessionAnalytics(
        total_sessions=1,
        active_sessions=1 if session.is_active else 0,
        archived_sessions=1 if session.is_archived else 0,
        total_turns=len(turns),
        total_cost=total_cost,
        average_cost_per_session=total_cost,
        average_turns_per_session=len(turns),
        most_used_models=[{"model": model, "usage": 1} for model in models_used],
        model_preference_stats=model_preference_stats
    )


@router.get("/{session_id}/export", response_model=SessionExport)
async def export_session(
    session_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
    export_format: str = Query("json", regex="^(json|markdown|csv)$"),
):
    """Export a session with all its data."""
    # Verify session ownership
    session_query = select(Session).where(
        and_(Session.id == session_id, Session.user_id == current_user.id)
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get turns
    turns_query = select(Turn).where(Turn.session_id == session_id).order_by(Turn.turn_number)
    turns_result = await db.execute(turns_query)
    turns = turns_result.scalars().all()
    
    # Get preferences
    preferences_query = select(Preference).where(Preference.session_id == session_id)
    preferences_result = await db.execute(preferences_query)
    preferences = preferences_result.scalars().all()
    
    return SessionExport(
        session=session,
        turns=turns,
        preferences=preferences,
        export_format=export_format
    )