import { 
  RunStatus, 
  TurnStatus, 
  OutputType,
  Session,
  SessionCreate,
  Turn,
  Run,
  WSMessage,
  AgentVariation
} from '@/lib/types'

describe('Types', () => {
  describe('RunStatus', () => {
    it('should include all expected statuses', () => {
      const statuses: RunStatus[] = ["pending", "running", "completed", "failed", "cancelled"]
      expect(statuses).toHaveLength(5)
    })
  })

  describe('TurnStatus', () => {
    it('should include all expected statuses', () => {
      const statuses: TurnStatus[] = ["pending", "streaming", "completed", "failed"]
      expect(statuses).toHaveLength(4)
    })
  })

  describe('OutputType', () => {
    it('should include all expected types', () => {
      const types: OutputType[] = ["llm", "stdout", "stderr", "status", "system", "summary", "diffs", "logging", "addinfo"]
      expect(types).toHaveLength(9)
    })
  })

  describe('Session interface', () => {
    it('should create valid session object', () => {
      const session: Session = {
        id: 'test-id',
        user_id: 'user-123',
        title: 'Test Session',
        description: 'A test session',
        is_active: true,
        is_archived: false,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
        last_activity_at: '2023-01-01T00:00:00Z',
        models_used: ['gpt-4', 'claude-3'],
        total_turns: 5,
        total_cost: 10.50
      }
      
      expect(session.id).toBe('test-id')
      expect(session.models_used).toHaveLength(2)
      expect(session.total_cost).toBe(10.50)
    })
  })

  describe('SessionCreate interface', () => {
    it('should create valid session create object', () => {
      const sessionCreate: SessionCreate = {
        title: 'New Session',
        description: 'A new session',
        models_used: ['gpt-4']
      }
      
      expect(sessionCreate.title).toBe('New Session')
      expect(sessionCreate.models_used).toContain('gpt-4')
    })

    it('should handle optional description', () => {
      const sessionCreate: SessionCreate = {
        title: 'New Session',
        models_used: ['gpt-4']
      }
      
      expect(sessionCreate.description).toBeUndefined()
    })
  })

  describe('Turn interface', () => {
    it('should create valid turn object', () => {
      const turn: Turn = {
        id: 'turn-123',
        session_id: 'session-456',
        user_id: 'user-789',
        turn_number: 1,
        prompt: 'Test prompt',
        model: 'gpt-4',
        models_requested: ['gpt-4', 'claude-3'],
        responses: { 'gpt-4': 'Response 1' },
        started_at: '2023-01-01T00:00:00Z',
        total_cost: 5.25,
        status: 'completed'
      }
      
      expect(turn.turn_number).toBe(1)
      expect(turn.status).toBe('completed')
      expect(turn.models_requested).toHaveLength(2)
    })
  })

  describe('Run interface', () => {
    it('should create valid run object', () => {
      const run: Run = {
        id: 'run-abc',
        github_url: 'https://github.com/test/repo',
        prompt: 'Test prompt',
        variations: 3,
        status: 'running',
        created_at: '2023-01-01T00:00:00Z',
        agent_config: { temperature: 0.7 },
        results: {}
      }
      
      expect(run.variations).toBe(3)
      expect(run.status).toBe('running')
      expect(run.github_url).toContain('github.com')
    })
  })

  describe('WSMessage interface', () => {
    it('should create valid websocket message', () => {
      const message: WSMessage = {
        type: 'llm',
        message_id: 'msg-123',
        data: {
          run_id: 'run-456',
          variation_id: '1',
          content: 'Test content',
          timestamp: '2023-01-01T00:00:00Z'
        }
      }
      
      expect(message.type).toBe('llm')
      expect(message.data.variation_id).toBe('1')
      expect(message.data.content).toBe('Test content')
    })

    it('should handle all message types', () => {
      const types: WSMessage['type'][] = ["connected", "llm", "stdout", "stderr", "status", "control_ack", "error", "pong"]
      expect(types).toHaveLength(8)
    })
  })

  describe('AgentVariation interface', () => {
    it('should create valid agent variation', () => {
      const variation: AgentVariation = {
        id: 'var-123',
        variation_id: 1,
        model_name: 'gpt-4',
        status: 'running',
        outputs: ['Output 1', 'Output 2'],
        progress: 50
      }
      
      expect(variation.variation_id).toBe(1)
      expect(variation.outputs).toHaveLength(2)
      expect(variation.progress).toBe(50)
    })

    it('should handle optional fields', () => {
      const variation: AgentVariation = {
        id: 'var-123',
        variation_id: 1,
        model_name: 'gpt-4',
        status: 'completed',
        outputs: []
      }
      
      expect(variation.progress).toBeUndefined()
      expect(variation.error).toBeUndefined()
    })
  })
})