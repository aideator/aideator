export interface DiffData {
  oldFile: {
    fileName: string;
    content: string;
    fileLang?: string;
  };
  newFile: {
    fileName: string;
    content: string;
    fileLang?: string;
  };
  hunks?: string[];
}

export const sampleDiffData: DiffData = {
  oldFile: {
    fileName: "UserService.ts",
    content: `import { User } from './types';

export class UserService {
  private users: User[] = [];

  constructor() {
    this.users = [];
  }

  getUser(id: string): User | undefined {
    return this.users.find(u => u.id === id);
  }

  addUser(user: User): void {
    this.users.push(user);
  }

  removeUser(id: string): void {
    const index = this.users.findIndex(u => u.id === id);
    if (index !== -1) {
      this.users.splice(index, 1);
    }
  }
}`,
    fileLang: "typescript"
  },
  newFile: {
    fileName: "UserService.ts",
    content: `import { User } from './types';
import { Logger } from './logger';

export class UserService {
  private users: Map<string, User> = new Map();
  private logger: Logger;

  constructor(logger: Logger) {
    this.users = new Map();
    this.logger = logger;
  }

  getUser(id: string): User | undefined {
    this.logger.log(\`Getting user \${id}\`);
    return this.users.get(id);
  }

  addUser(user: User): void {
    this.logger.log(\`Adding user \${user.id}\`);
    this.users.set(user.id, user);
  }

  removeUser(id: string): boolean {
    this.logger.log(\`Removing user \${id}\`);
    return this.users.delete(id);
  }

  getAllUsers(): User[] {
    return Array.from(this.users.values());
  }
}`,
    fileLang: "typescript"
  }
};

export const sampleGitDiffData: DiffData = {
  oldFile: {
    fileName: "package.json",
    content: "",
    fileLang: "json"
  },
  newFile: {
    fileName: "package.json", 
    content: "",
    fileLang: "json"
  },
  hunks: [
    "@@ -1,12 +1,15 @@",
    " {",
    '   "name": "my-app",',
    '-  "version": "1.0.0",',
    '+  "version": "1.1.0",',
    '   "dependencies": {',
    '-    "react": "^17.0.2",',
    '-    "react-dom": "^17.0.2"',
    '+    "react": "^18.0.0",',
    '+    "react-dom": "^18.0.0",',
    '+    "@git-diff-view/react": "^0.0.27"',
    '   },',
    '   "scripts": {',
    '     "start": "react-scripts start",',
    '-    "build": "react-scripts build"',
    '+    "build": "react-scripts build",',
    '+    "test": "react-scripts test"',
    '   }',
    ' }'
  ]
};