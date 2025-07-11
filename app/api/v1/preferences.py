from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.core.database import get_session
from app.core.dependencies import CurrentUser
from app.models.session import Preference, Session, Turn
from app.schemas.session import (
    ModelPerformanceMetrics,
    PreferenceResponse,
)

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("/", response_model=list[PreferenceResponse])
async def get_user_preferences(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    model_filter: str | None = Query(None),
    preference_type: str | None = Query(None),
) -> list[PreferenceResponse]:
    """Get user's preferences with filtering and pagination."""
    query = select(Preference).where(col(Preference.user_id) == current_user.id)

    if model_filter:
        query = query.where(col(Preference.preferred_model) == model_filter)

    if preference_type:
        query = query.where(col(Preference.preference_type) == preference_type)

    query = query.order_by(desc(col(Preference.created_at))).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/stats", response_model=dict[str, Any])
async def get_preference_stats(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
    days: int = Query(30, ge=1, le=365),
) -> dict[str, Any]:
    """Get user's preference statistics."""
    # Get preferences from the last N days
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    query = select(Preference).where(
        and_(
            col(Preference.user_id) == current_user.id,
            col(Preference.created_at) >= cutoff_date,
        )
    )
    result = await db.execute(query)
    preferences = result.scalars().all()

    if not preferences:
        return {
            "total_preferences": 0,
            "model_win_rates": {},
            "average_confidence": 0,
            "preference_types": {},
            "quality_scores": {},
        }

    # Calculate stats
    total_preferences = len(preferences)
    model_wins: dict[str, int] = {}
    confidence_scores: list[int] = []
    preference_types: dict[str, int] = {}
    quality_scores: dict[str, list[int]] = {}

    for pref in preferences:
        # Model wins
        model_wins[pref.preferred_model] = model_wins.get(pref.preferred_model, 0) + 1

        # Confidence scores
        if pref.confidence_score:
            confidence_scores.append(pref.confidence_score)

        # Preference types
        preference_types[pref.preference_type] = (
            preference_types.get(pref.preference_type, 0) + 1
        )

        # Quality scores
        for model, score in pref.response_quality_scores.items():
            if model not in quality_scores:
                quality_scores[model] = []
            quality_scores[model].append(score)

    # Calculate win rates
    model_win_rates = {}
    for model, wins in model_wins.items():
        model_win_rates[model] = wins / total_preferences

    # Calculate average quality scores
    avg_quality_scores = {}
    for model, scores in quality_scores.items():
        avg_quality_scores[model] = sum(scores) / len(scores)

    return {
        "total_preferences": total_preferences,
        "model_win_rates": model_win_rates,
        "average_confidence": sum(confidence_scores) / len(confidence_scores)
        if confidence_scores
        else 0,
        "preference_types": preference_types,
        "quality_scores": avg_quality_scores,
        "days_analyzed": days,
    }


@router.get("/models/performance", response_model=list[ModelPerformanceMetrics])
async def get_model_performance(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
    days: int = Query(30, ge=1, le=365),
) -> list[ModelPerformanceMetrics]:
    """Get model performance metrics based on user preferences."""
    # Get preferences from the last N days
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    preferences_query = select(Preference).where(
        and_(
            col(Preference.user_id) == current_user.id,
            col(Preference.created_at) >= cutoff_date,
        )
    )
    preferences_result = await db.execute(preferences_query)
    preferences = preferences_result.scalars().all()

    # Get turns for response time analysis
    turns_query = (
        select(Turn)
        .join(Session)
        .where(
            and_(
                col(Session.user_id) == current_user.id,
                col(Turn.started_at) >= cutoff_date,
                col(Turn.status) == "completed",
            )
        )
    )
    turns_result = await db.execute(turns_query)
    turns = turns_result.scalars().all()

    # Analyze model performance
    model_stats: dict[str, dict[str, Any]] = {}

    # Process turns for request counts and response times
    for turn in turns:
        for model in turn.models_requested:
            if model not in model_stats:
                model_stats[model] = {
                    "requests": 0,
                    "total_cost": 0,
                    "response_times": [],
                    "wins": 0,
                    "quality_scores": [],
                }

            model_stats[model]["requests"] += 1
            model_stats[model]["total_cost"] += turn.total_cost / len(
                turn.models_requested
            )

            if turn.duration_seconds:
                model_stats[model]["response_times"].append(turn.duration_seconds)

    # Process preferences for win rates and quality scores
    for pref in preferences:
        # Count wins
        if pref.preferred_model in model_stats:
            model_stats[pref.preferred_model]["wins"] += 1

        # Add quality scores
        for model, score in pref.response_quality_scores.items():
            if model in model_stats:
                model_stats[model]["quality_scores"].append(score)

    # Calculate metrics
    metrics = []
    total_requests = sum(stats["requests"] for stats in model_stats.values())
    total_preferences = len(preferences)

    for model, stats in model_stats.items():
        if stats["requests"] > 0:
            avg_response_time = (
                sum(stats["response_times"]) / len(stats["response_times"])
                if stats["response_times"]
                else 0
            )

            preference_win_rate = (
                stats["wins"] / total_preferences if total_preferences > 0 else 0
            )

            avg_quality_score = (
                sum(stats["quality_scores"]) / len(stats["quality_scores"])
                if stats["quality_scores"]
                else 0
            )

            usage_percentage = (
                stats["requests"] / total_requests if total_requests > 0 else 0
            )

            metrics.append(
                ModelPerformanceMetrics(
                    model_name=model,
                    total_requests=stats["requests"],
                    total_cost=stats["total_cost"],
                    average_response_time=avg_response_time,
                    preference_win_rate=preference_win_rate,
                    average_quality_score=avg_quality_score,
                    usage_percentage=usage_percentage,
                )
            )

    # Sort by win rate descending
    metrics.sort(key=lambda x: x.preference_win_rate, reverse=True)

    return metrics


@router.get("/trends", response_model=dict[str, Any])
async def get_preference_trends(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
    days: int = Query(30, ge=7, le=365),
) -> dict[str, Any]:
    """Get preference trends over time."""
    # Get preferences from the last N days
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    query = (
        select(Preference)
        .where(
            and_(
                col(Preference.user_id) == current_user.id,
                col(Preference.created_at) >= cutoff_date,
            )
        )
        .order_by(col(Preference.created_at))
    )

    result = await db.execute(query)
    preferences = result.scalars().all()

    if not preferences:
        return {
            "daily_preferences": [],
            "model_trend": {},
            "confidence_trend": [],
            "quality_trend": {},
        }

    # Group preferences by day
    daily_preferences: dict[str, int] = {}
    model_daily_wins: dict[str, dict[str, int]] = {}
    daily_confidence: dict[str, list[int]] = {}
    daily_quality: dict[str, dict[str, list[int]]] = {}

    for pref in preferences:
        day_key = pref.created_at.date().isoformat()

        # Count daily preferences
        daily_preferences[day_key] = daily_preferences.get(day_key, 0) + 1

        # Track model wins by day
        if day_key not in model_daily_wins:
            model_daily_wins[day_key] = {}
        model_daily_wins[day_key][pref.preferred_model] = (
            model_daily_wins[day_key].get(pref.preferred_model, 0) + 1
        )

        # Track confidence by day
        if pref.confidence_score:
            if day_key not in daily_confidence:
                daily_confidence[day_key] = []
            daily_confidence[day_key].append(pref.confidence_score)

        # Track quality scores by day
        if day_key not in daily_quality:
            daily_quality[day_key] = {}
        for model, score in pref.response_quality_scores.items():
            if model not in daily_quality[day_key]:
                daily_quality[day_key][model] = []
            daily_quality[day_key][model].append(score)

    # Calculate trends
    daily_prefs_trend = [
        {"date": date, "count": count}
        for date, count in sorted(daily_preferences.items())
    ]

    confidence_trend = [
        {"date": date, "average_confidence": sum(scores) / len(scores)}
        for date, scores in sorted(daily_confidence.items())
    ]

    # Calculate daily average quality scores
    quality_trend = {}
    for date, models in daily_quality.items():
        quality_trend[date] = {
            model: sum(scores) / len(scores) for model, scores in models.items()
        }

    return {
        "daily_preferences": daily_prefs_trend,
        "model_trend": model_daily_wins,
        "confidence_trend": confidence_trend,
        "quality_trend": quality_trend,
        "days_analyzed": days,
    }


@router.delete("/{preference_id}")
async def delete_preference(
    preference_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Delete a preference."""
    query = select(Preference).where(
        and_(
            col(Preference.id) == preference_id,
            col(Preference.user_id) == current_user.id,
        )
    )
    result = await db.execute(query)
    preference = result.scalar_one_or_none()

    if not preference:
        raise HTTPException(status_code=404, detail="Preference not found")

    await db.delete(preference)
    await db.commit()

    return {"message": "Preference deleted successfully"}
