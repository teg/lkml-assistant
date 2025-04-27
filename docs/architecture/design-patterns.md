# Design Patterns

This document outlines the key design patterns used in the LKML Assistant application.

## Repository Pattern

### Overview

The Repository Pattern is a central design pattern in this application, providing an abstraction layer between the domain model and data access logic.

```
[Business Logic] → [Repository Interface] → [Repository Implementation] → [Data Source]
```

### Implementation

```typescript
// Repository interface
interface PatchRepository {
  findById(id: string): Promise<Patch | null>;
  findByMessageId(messageId: string): Promise<Patch | null>;
  findAll(limit?: number): Promise<Patch[]>;
  findByDateRange(startDate: string, endDate: string): Promise<Patch[]>;
  findBySeries(seriesId: string): Promise<Patch[]>;
  save(patch: Patch): Promise<void>;
  update(patch: Patch): Promise<void>;
  delete(id: string): Promise<void>;
}

// DynamoDB implementation
class DynamoDBPatchRepository implements PatchRepository {
  constructor(private readonly docClient: DynamoDB.DocumentClient) {}
  
  async findById(id: string): Promise<Patch | null> {
    // Implementation using DynamoDB operations
  }
  
  // Other method implementations...
}
```

### Benefits

- **Separation of concerns**: Business logic is decoupled from data access
- **Testability**: Easy to mock repositories for testing business logic
- **Flexibility**: Can switch data sources without modifying business logic
- **Consistency**: Common data access patterns across the application

## Factory Pattern

### Overview

The Factory Pattern is used to create instances of repositories and other components without exposing the creation logic.

```typescript
// Repository factory
class RepositoryFactory {
  private static patchRepository: PatchRepository;
  private static discussionRepository: DiscussionRepository;
  
  static getPatchRepository(): PatchRepository {
    if (!RepositoryFactory.patchRepository) {
      const docClient = new DynamoDB.DocumentClient();
      RepositoryFactory.patchRepository = new DynamoDBPatchRepository(docClient);
    }
    return RepositoryFactory.patchRepository;
  }
  
  static getDiscussionRepository(): DiscussionRepository {
    // Similar implementation
  }
}
```

## Adapter Pattern

### Overview

The Adapter Pattern is used to convert external API responses to internal domain models.

```typescript
// Patchwork API adapter
class PatchworkAdapter {
  static toDomainModel(patchworkPatch: PatchworkPatch): Patch {
    return {
      id: patchworkPatch.id.toString(),
      submitterId: patchworkPatch.submitter.id.toString(),
      submitterName: patchworkPatch.submitter.name,
      submitterEmail: patchworkPatch.submitter.email,
      subject: patchworkPatch.name,
      date: patchworkPatch.date,
      messageId: patchworkPatch.msgid,
      url: patchworkPatch.web_url,
      state: this.mapState(patchworkPatch.state),
      project: patchworkPatch.project.name,
      series: patchworkPatch.series.length > 0 ? {
        id: patchworkPatch.series[0].id.toString(),
        name: patchworkPatch.series[0].name,
        version: patchworkPatch.series[0].version,
        partIndex: 0, // To be set later
        totalParts: 0  // To be set later
      } : null,
      tags: [],
      coverLetter: null,
      content: "", // To be filled later
      isRustRelated: false, // To be determined later
      lastUpdated: new Date().toISOString()
    };
  }
  
  private static mapState(state: string): PatchState {
    // Map Patchwork state to internal PatchState
  }
}
```

## Strategy Pattern

### Overview

The Strategy Pattern is used for processing patches and discussions with different strategies based on context.

```typescript
// Strategy interface
interface PatchProcessingStrategy {
  process(patch: Patch): Promise<ProcessingResult>;
}

// Concrete strategies
class RustPatchProcessingStrategy implements PatchProcessingStrategy {
  async process(patch: Patch): Promise<ProcessingResult> {
    // Special processing for Rust-related patches
  }
}

class StandardPatchProcessingStrategy implements PatchProcessingStrategy {
  async process(patch: Patch): Promise<ProcessingResult> {
    // Standard processing for regular patches
  }
}

// Strategy selector
class PatchProcessor {
  process(patch: Patch): Promise<ProcessingResult> {
    const strategy = patch.isRustRelated
      ? new RustPatchProcessingStrategy()
      : new StandardPatchProcessingStrategy();
    
    return strategy.process(patch);
  }
}
```

## Observer Pattern

### Overview

The Observer Pattern is implemented through EventBridge for event-driven communication between components.

```typescript
// Event publisher (simplified)
class PatchEventPublisher {
  private readonly eventBridge: AWS.EventBridge;
  
  constructor() {
    this.eventBridge = new AWS.EventBridge();
  }
  
  async publishPatchCreated(patch: Patch): Promise<void> {
    await this.eventBridge.putEvents({
      Entries: [{
        Source: 'lkml-assistant.patch',
        DetailType: 'PatchCreated',
        Detail: JSON.stringify(patch),
        EventBusName: process.env.EVENT_BUS_NAME
      }]
    }).promise();
  }
  
  // Other event publishing methods...
}

// Event subscriber (in Lambda handler)
export const handlePatchCreated = async (event: any): Promise<void> {
  const patch: Patch = JSON.parse(event.detail);
  // Process the patch
};
```

## Singleton Pattern

### Overview

The Singleton Pattern ensures only one instance of a resource-intensive object exists.

```typescript
// Singleton DynamoDB client
class DynamoDBClient {
  private static instance: AWS.DynamoDB.DocumentClient;
  
  private constructor() {}
  
  static getInstance(): AWS.DynamoDB.DocumentClient {
    if (!DynamoDBClient.instance) {
      DynamoDBClient.instance = new AWS.DynamoDB.DocumentClient();
    }
    return DynamoDBClient.instance;
  }
}
```

## Decorator Pattern

### Overview

The Decorator Pattern adds functionality to repositories, such as caching or logging.

```typescript
// Base repository
class BasePatchRepository implements PatchRepository {
  // Implementation of PatchRepository methods
}

// Caching decorator
class CachingPatchRepository implements PatchRepository {
  private readonly repository: PatchRepository;
  private readonly cache: Map<string, Patch>;
  
  constructor(repository: PatchRepository) {
    this.repository = repository;
    this.cache = new Map();
  }
  
  async findById(id: string): Promise<Patch | null> {
    if (this.cache.has(id)) {
      return this.cache.get(id) || null;
    }
    
    const patch = await this.repository.findById(id);
    
    if (patch) {
      this.cache.set(id, patch);
    }
    
    return patch;
  }
  
  // Other method implementations with caching...
}

// Creating a repository with decorators
const patchRepository = new CachingPatchRepository(
  new LoggingPatchRepository(
    new BasePatchRepository()
  )
);
```

## Circuit Breaker Pattern

### Overview

The Circuit Breaker Pattern prevents cascading failures when external services are unavailable.

```typescript
class CircuitBreaker {
  private failures: number = 0;
  private lastFailureTime: number = 0;
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
  
  constructor(
    private readonly failureThreshold: number = 3,
    private readonly resetTimeout: number = 30000 // 30 seconds
  ) {}
  
  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      // Check if reset timeout has elapsed
      if (Date.now() - this.lastFailureTime > this.resetTimeout) {
        this.state = 'HALF_OPEN';
      } else {
        throw new Error('Circuit breaker is open');
      }
    }
    
    try {
      const result = await operation();
      this.reset();
      return result;
    } catch (error) {
      this.recordFailure();
      throw error;
    }
  }
  
  private reset(): void {
    this.failures = 0;
    this.state = 'CLOSED';
  }
  
  private recordFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();
    
    if (this.failures >= this.failureThreshold) {
      this.state = 'OPEN';
    }
  }
}

// Usage with API client
class PatchworkClient {
  private circuitBreaker = new CircuitBreaker();
  
  async fetchPatches(): Promise<PatchworkPatch[]> {
    return this.circuitBreaker.execute(async () => {
      // API call implementation
    });
  }
}
```

## Command Pattern

### Overview

The Command Pattern encapsulates operations as objects, allowing for parameterization and queueing.

```typescript
// Command interface
interface Command {
  execute(): Promise<void>;
}

// Concrete commands
class FetchPatchesCommand implements Command {
  constructor(
    private readonly patchworkClient: PatchworkClient,
    private readonly patchRepository: PatchRepository
  ) {}
  
  async execute(): Promise<void> {
    const patches = await this.patchworkClient.fetchPatches();
    // Process and save patches
  }
}

// Command executor
class CommandExecutor {
  private readonly commands: Command[] = [];
  
  addCommand(command: Command): void {
    this.commands.push(command);
  }
  
  async executeAll(): Promise<void> {
    for (const command of this.commands) {
      await command.execute();
    }
  }
}
```

## Dependency Injection

### Overview

Dependency Injection provides components with their dependencies rather than having them create dependencies themselves.

```typescript
// Lambda factory with dependency injection
function createPatchFetcherHandler(
  patchworkClient: PatchworkClient,
  patchRepository: PatchRepository
) {
  return async (event: any): Promise<void> => {
    const patches = await patchworkClient.fetchPatches();
    // Process and save patches using patchRepository
  };
}

// Usage with real implementations
const handler = createPatchFetcherHandler(
  new RealPatchworkClient(),
  new DynamoDBPatchRepository(new AWS.DynamoDB.DocumentClient())
);

// Usage with mock implementations for testing
const testHandler = createPatchFetcherHandler(
  new MockPatchworkClient(),
  new InMemoryPatchRepository()
);
```

## Conclusion

These design patterns provide a solid foundation for the LKML Assistant application, ensuring:

1. **Maintainability**: Through separation of concerns and modular design
2. **Testability**: By allowing easy mocking and isolation of components
3. **Flexibility**: To adapt to changing requirements and integration points
4. **Scalability**: By enabling efficient resource use and consistent patterns
5. **Resilience**: Through patterns like Circuit Breaker that handle failures gracefully