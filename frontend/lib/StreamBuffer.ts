/**
 * StreamBuffer - Smooth streaming buffer for agent outputs
 * 
 * This class provides ChatGPT-like smooth streaming by:
 * - Buffering incoming tokens
 * - Draining at a consistent rate (40-60 tokens/second)
 * - Respecting word boundaries (never splitting words)
 * - Handling markdown blocks properly
 * - Providing pause/resume capabilities
 */

export interface StreamBufferOptions {
  // Target tokens per second (default: 50)
  tokensPerSecond?: number;
  // Minimum chunk size before starting to drain (default: 10)
  minChunkSize?: number;
  // Maximum buffer size before forcing drain (default: 1000)
  maxBufferSize?: number;
  // Whether to respect word boundaries (default: true)
  respectWordBoundaries?: boolean;
  // Whether to respect markdown blocks (default: true)
  respectMarkdownBlocks?: boolean;
}

export interface StreamBufferCallbacks {
  onToken: (token: string) => void;
  onFlush?: () => void;
  onPause?: () => void;
  onResume?: () => void;
}

export class StreamBuffer {
  private buffer: string = '';
  private drainInterval: NodeJS.Timeout | null = null;
  private isPaused: boolean = false;
  private isComplete: boolean = false;
  
  private options: Required<StreamBufferOptions>;
  private callbacks: StreamBufferCallbacks;
  
  // Markdown block tracking
  private inCodeBlock: boolean = false;
  private inTable: boolean = false;
  private pendingListItem: boolean = false;
  
  constructor(callbacks: StreamBufferCallbacks, options: StreamBufferOptions = {}) {
    this.callbacks = callbacks;
    this.options = {
      tokensPerSecond: options.tokensPerSecond ?? 50,
      minChunkSize: options.minChunkSize ?? 10,
      maxBufferSize: options.maxBufferSize ?? 1000,
      respectWordBoundaries: options.respectWordBoundaries ?? true,
      respectMarkdownBlocks: options.respectMarkdownBlocks ?? true,
    };
    
    this.startDraining();
  }
  
  /**
   * Add content to the buffer
   */
  add(content: string): void {
    if (this.isComplete) return;
    this.buffer += content;
    
    // Force drain if buffer is too large
    if (this.buffer.length > this.options.maxBufferSize) {
      this.drainImmediate();
    }
  }
  
  /**
   * Complete the stream and flush remaining content
   */
  complete(): void {
    this.isComplete = true;
    this.flush();
  }
  
  /**
   * Pause the draining process
   */
  pause(): void {
    if (!this.isPaused) {
      this.isPaused = true;
      this.callbacks.onPause?.();
    }
  }
  
  /**
   * Resume the draining process
   */
  resume(): void {
    if (this.isPaused) {
      this.isPaused = false;
      this.callbacks.onResume?.();
    }
  }
  
  /**
   * Destroy the buffer and clean up
   */
  destroy(): void {
    if (this.drainInterval) {
      cancelAnimationFrame(this.drainInterval as number);
      this.drainInterval = null;
    }
    this.flush();
  }
  
  /**
   * Start the draining process using requestAnimationFrame for smooth rendering
   */
  private startDraining(): void {
    const msPerToken = 1000 / this.options.tokensPerSecond;
    let lastDrainTime = 0;
    
    const animationLoop = (currentTime: number) => {
      if (this.drainInterval === null) return; // Stop if destroyed
      
      // Calculate if enough time has passed for next token
      if (currentTime - lastDrainTime >= msPerToken) {
        if (!this.isPaused && this.buffer.length > 0) {
          this.drain();
          lastDrainTime = currentTime;
        }
      }
      
      // Continue the loop
      this.drainInterval = requestAnimationFrame(animationLoop) as any;
    };
    
    this.drainInterval = requestAnimationFrame(animationLoop) as any;
  }
  
  /**
   * Drain one token from the buffer
   */
  private drain(): void {
    if (this.buffer.length === 0) return;
    
    // Wait for minimum chunk size unless complete
    if (!this.isComplete && this.buffer.length < this.options.minChunkSize) {
      return;
    }
    
    let tokenToDrain = '';
    
    if (this.options.respectMarkdownBlocks) {
      tokenToDrain = this.getNextMarkdownAwareToken();
    } else if (this.options.respectWordBoundaries) {
      tokenToDrain = this.getNextWordBoundaryToken();
    } else {
      // Simple character-by-character draining
      tokenToDrain = this.buffer[0];
      this.buffer = this.buffer.slice(1);
    }
    
    if (tokenToDrain) {
      this.callbacks.onToken(tokenToDrain);
    }
  }
  
  /**
   * Get the next token respecting markdown structure
   */
  private getNextMarkdownAwareToken(): string {
    // Check for code block markers
    if (this.buffer.startsWith('```')) {
      const endIndex = this.buffer.indexOf('\n', 3);
      if (endIndex !== -1) {
        const token = this.buffer.slice(0, endIndex + 1);
        this.buffer = this.buffer.slice(endIndex + 1);
        this.inCodeBlock = !this.inCodeBlock;
        return token;
      }
    }
    
    // Inside code block - drain line by line
    if (this.inCodeBlock) {
      const newlineIndex = this.buffer.indexOf('\n');
      if (newlineIndex !== -1) {
        const token = this.buffer.slice(0, newlineIndex + 1);
        this.buffer = this.buffer.slice(newlineIndex + 1);
        return token;
      }
      // If no newline and stream is complete, drain everything
      if (this.isComplete) {
        const token = this.buffer;
        this.buffer = '';
        return token;
      }
      return '';
    }
    
    // Check for table markers
    if (this.buffer.startsWith('|')) {
      const lineEnd = this.buffer.indexOf('\n');
      if (lineEnd !== -1) {
        const token = this.buffer.slice(0, lineEnd + 1);
        this.buffer = this.buffer.slice(lineEnd + 1);
        return token;
      }
    }
    
    // Check for list items
    if (this.buffer.match(/^[\s]*[-*+]\s/) || this.buffer.match(/^[\s]*\d+\.\s/)) {
      const lineEnd = this.buffer.indexOf('\n');
      if (lineEnd !== -1) {
        const token = this.buffer.slice(0, lineEnd + 1);
        this.buffer = this.buffer.slice(lineEnd + 1);
        return token;
      }
    }
    
    // Check for headers
    if (this.buffer.match(/^#{1,6}\s/)) {
      const lineEnd = this.buffer.indexOf('\n');
      if (lineEnd !== -1) {
        const token = this.buffer.slice(0, lineEnd + 1);
        this.buffer = this.buffer.slice(lineEnd + 1);
        return token;
      }
    }
    
    // Default to word boundary logic
    return this.getNextWordBoundaryToken();
  }
  
  /**
   * Get the next token respecting word boundaries
   */
  private getNextWordBoundaryToken(): string {
    if (this.buffer.length === 0) return '';
    
    // Simplified approach for smoother streaming:
    // 1. If buffer starts with whitespace, take all consecutive whitespace
    if (/^\s/.test(this.buffer)) {
      const match = this.buffer.match(/^\s+/);
      if (match) {
        const token = match[0];
        this.buffer = this.buffer.slice(token.length);
        return token;
      }
    }
    
    // 2. For regular text, take 2-5 characters at a time for smoother appearance
    let chunkSize = Math.min(3, this.buffer.length);
    
    // Look for natural breaks within a reasonable distance
    const nearbyBoundary = this.buffer.slice(0, 8).search(/[\s.,!?;:]/);
    if (nearbyBoundary > 0 && nearbyBoundary <= 5) {
      chunkSize = nearbyBoundary + 1; // Include the boundary character
    }
    
    // If we're at the end and have a small buffer, just take it all
    if (this.isComplete && this.buffer.length <= 8) {
      chunkSize = this.buffer.length;
    }
    
    const token = this.buffer.slice(0, chunkSize);
    this.buffer = this.buffer.slice(chunkSize);
    return token;
  }
  
  /**
   * Drain immediately without respecting boundaries
   */
  private drainImmediate(): void {
    const toDrain = Math.min(100, this.buffer.length);
    const token = this.buffer.slice(0, toDrain);
    this.buffer = this.buffer.slice(toDrain);
    this.callbacks.onToken(token);
  }
  
  /**
   * Flush all remaining content
   */
  private flush(): void {
    if (this.buffer.length > 0) {
      this.callbacks.onToken(this.buffer);
      this.buffer = '';
    }
    this.callbacks.onFlush?.();
  }
  
  /**
   * Get current buffer size
   */
  getBufferSize(): number {
    return this.buffer.length;
  }
  
  /**
   * Check if buffer is empty
   */
  isEmpty(): boolean {
    return this.buffer.length === 0;
  }
}

export default StreamBuffer;