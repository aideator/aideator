# AIdeator MVP Requirements - Multi-Model Prompt Comparison Platform

## Overview

AIdeator is a **Multi-Model Prompt Comparison Platform** that combines Kubernetes orchestration with LiteLLM Gateway to enable users to run multiple AI models in parallel on the same prompt, compare their responses side by side, and gain rich analytics insights. By leveraging Kubernetes Jobs for true parallel execution and LiteLLM Gateway for unified API access and built-in analytics, we achieve both scalability and comprehensive observability without sacrificing performance.

## Core Value Proposition

Enable users to:
1. Submit a single prompt to multiple AI models simultaneously (3-4 models initially, scalable to 6)
2. View and compare responses side-by-side in a clean, intuitive interface
3. Select preferred responses and provide feedback on why
4. Maintain conversation context across multiple turns within sessions
5. Benefit from personalized recommendations based on their preferences over time

## MVP Feature Set (80/20 Rule)

### 1. Multi-Model Prompt Execution
- **True Parallel Execution**: Kubernetes Jobs run models simultaneously, not sequentially
- **LiteLLM Gateway Integration**: Unified API interface for 100+ model providers
- **Model Support**: OpenAI, Anthropic, Google, Cohere, local models, and more
- **BYOK (Bring Your Own Key)**: Encrypted storage of user API keys in PostgreSQL
- **Efficient Processing**: Each model runs in isolated container for true parallelism
- **Error Handling**: Gateway provides automatic retries and fallbacks

### 2. Side-by-Side Response Comparison UI
- **Responsive Grid Layout**: Up to 4 models displayed side-by-side on desktop
- **Model Identification**: Clear labeling with distinct color accents per model
- **Preference Selection**: "I prefer this response" button on each panel
- **Response Metrics**: Display response time, token count, and cost per model (via Gateway)
- **Scrollable Panels**: Handle long responses with bounded height and scrollbars
- **Progressive Disclosure**: Show/hide additional models beyond the first 4

### 3. Preference Logging and Feedback
- **One-Click Selection**: Simple preference recording without interrupting flow
- **Optional "Why" Feedback**: Text input for users to explain their choice
- **Data Capture**: Log prompt, all responses, chosen model, and feedback
- **Session Association**: Link preferences to specific sessions and users
- **Future-Ready**: Structure data for future ML/personalization features

### 4. Core Chat Loop Mechanics
- **Smooth UX Flow**: Prompt → Loading indicators → Responses → Selection → Next prompt
- **Real-time Feedback**: Show loading state per model during generation
- **Visual Confirmation**: Highlight selected response with gold outline/checkmark
- **Ready State**: Immediately ready for next prompt after selection
- **Non-blocking UI**: Interface remains responsive during model queries

### 5. Basic Session Management
- **Session Persistence**: Store conversation history in PostgreSQL (migrate from SQLite)
- **Session Sidebar**: List of current and past sessions (similar to ChatGPT)
- **Context Retention**: Remember prompts and chosen responses within sessions
- **Single-Model Continuation**: After first multi-model comparison, continue with chosen model
- **New Session Creation**: Simple "New Chat" button to start fresh conversations
- **Session Loading**: Click to restore and continue previous conversations

## Technical Architecture Updates

### Hybrid Architecture: Kubernetes + LiteLLM Gateway

#### Kubernetes Layer (Orchestration)
- **Parallel Jobs**: Each model runs in its own Kubernetes Job
- **Resource Isolation**: Container-level isolation for security and stability
- **Log Streaming**: kubectl logs streamed via SSE for real-time updates
- **Job Management**: TTL-based cleanup, resource limits, RBAC

#### LiteLLM Gateway Layer (Analytics & API)
- **Unified API**: Single interface for all model providers
- **Built-in Metrics**: Response times, token usage, costs, error rates
- **Prometheus Export**: Production-grade observability
- **Caching**: Redis-backed response caching
- **Rate Limiting**: Per-user and per-model controls

### Backend (FastAPI)
- **Model Comparison Service**: Orchestrates parallel Kubernetes Jobs
- **Gateway Integration**: Routes model calls through LiteLLM Gateway
- **PostgreSQL Database**: Sessions, preferences, and encrypted API keys
- **Session Management**: Context retention across conversations
- **Analytics API**: Exposes Gateway metrics and user preferences

### Frontend (Next.js 15)
- **Comparison Layout**: CSS Grid for responsive multi-panel display
- **Session UI**: Sidebar navigation for session management
- **Real-time Updates**: Maintain SSE for streaming responses
- **Preference Tracking**: Components for selection and feedback capture
- **Responsive Design**: Adapt from 4-column desktop to single-column mobile

### Data Model
```python
# Core entities
class User:
    id: UUID
    email: str
    created_at: datetime

class Session:
    id: UUID
    user_id: UUID
    title: str  # Auto-generated or user-provided
    created_at: datetime
    updated_at: datetime

class Turn:
    id: UUID
    session_id: UUID
    prompt: str
    turn_number: int
    created_at: datetime

class ModelResponse:
    id: UUID
    turn_id: UUID
    model_name: str
    response_text: str
    response_time_ms: int
    token_count: int
    cost_usd: float  # Tracked by LiteLLM Gateway
    created_at: datetime

class Preference:
    id: UUID
    turn_id: UUID
    chosen_model_response_id: UUID
    feedback_text: Optional[str]
    created_at: datetime
```

## UI/UX Principles

### Principle of Least Astonishment (POLA)
- **Familiar Patterns**: Mirror ChatGPT's interface layout and interactions
- **Standard Icons**: Use conventional symbols (+, trash, gear, etc.)
- **Predictable Behavior**: Actions do exactly what users expect
- **No Hidden Modes**: All functionality is discoverable and clear

### Visual Design (Tailwind CSS v4)
- **Clean Aesthetic**: Minimal, distraction-free interface
- **Model Differentiation**: Subtle color coding for each model's panel
- **Consistent Styling**: Unified design system across all components
- **Focus on Content**: Conversation is the primary visual element
- **Accessibility**: Keyboard navigation and ARIA labels

## MVP Analytics (Built-in via LiteLLM Gateway)

1. **Model Performance Metrics**: Response times, token usage, costs (Prometheus)
2. **User Preference Tracking**: Win rates by model, feedback analysis
3. **Session Analytics**: Duration, turn count, model switching patterns
4. **Real-time Monitoring**: Live metrics during comparisons
5. **Cost Analysis**: Per-model and per-user spending tracked automatically

## MVP Exclusions (Post-MVP Features)

1. **Multi-Model Multi-Turn**: Continuing with all models in parallel (complexity)
2. **Custom Analytics Dashboards**: Grafana integration for advanced visualization
3. **Branching Conversations**: Forking sessions to explore alternatives
4. **Automated Personalization**: ML-based response ranking/filtering
5. **Prompt Engineering Assistant**: AI-powered prompt improvement suggestions
6. **Mobile-First Design**: Initial focus is desktop, mobile is secondary

## Success Metrics

1. **Core Functionality**: Users can compare 3-4 model responses seamlessly
2. **Performance**: All model responses return within 10 seconds
3. **Usability**: New users can complete first comparison without instructions
4. **Data Collection**: 100% of preferences are successfully logged
5. **Session Continuity**: Users can resume conversations across sessions
6. **Stability**: <1% error rate on model queries and preference recording

## Hybrid Architecture Components

### Keep (From Current System)
- FastAPI backend framework
- Next.js 15 frontend with TypeScript 5  
- Tailwind CSS v4 design system
- SSE for real-time streaming
- User authentication system
- **Kubernetes Jobs for parallel execution**
- **kubectl log streaming for real-time updates**
- **Helm charts for deployment**
- **Tilt for local development**

### Add (New Components)
- LiteLLM Gateway deployment (via Helm)
- Redis for Gateway caching
- PostgreSQL database (fresh implementation)
- Session management system
- Preference tracking components
- Multi-model comparison UI
- Analytics API endpoints
- Prometheus metrics collection

### Integration Points
- Agent containers call LiteLLM Gateway instead of direct APIs
- Gateway provides unified interface + analytics
- Kubernetes maintains parallel execution advantage
- PostgreSQL stores sessions, preferences, and encrypted keys

## Development Priorities

### Phase 1: Core Infrastructure (Week 1)
- [ ] Deploy LiteLLM Gateway via Helm chart
- [ ] Update agent containers to use Gateway
- [ ] Implement PostgreSQL schema and models
- [ ] Create session management APIs
- [ ] Set up Prometheus metrics collection

### Phase 2: MVP Features (Week 2-3)
- [ ] Build preference selection and logging system
- [ ] Implement session sidebar and navigation
- [ ] Display Gateway metrics (time, tokens, cost)
- [ ] Create smooth loading states and error handling

### Phase 3: Polish & Testing (Week 4)
- [ ] Refine UI/UX based on POLA principles
- [ ] Add keyboard shortcuts and accessibility
- [ ] Comprehensive error handling
- [ ] End-to-end testing of full flow

## Technical Constraints

1. **API Rate Limits**: Handle model-specific rate limiting gracefully
2. **Response Times**: Optimize for slowest model in the set
3. **Context Limits**: Manage conversation length within model constraints
4. **Cost Management**: Clear visibility of API usage per model
5. **Security**: Encrypted storage of API keys, secure session management

## Deliverables

1. **Backend API**: FastAPI orchestrating Kubernetes Jobs + LiteLLM Gateway
2. **Frontend App**: Next.js interface for multi-model comparison
3. **Infrastructure**: Helm charts including LiteLLM Gateway + Redis
4. **Database Schema**: PostgreSQL with sessions, preferences, analytics
5. **Observability**: Prometheus metrics + Gateway analytics
6. **Documentation**: Architecture, deployment, and user guides