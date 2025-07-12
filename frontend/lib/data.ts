type DiffLine = {
  type: "add" | "del" | "normal"
  oldLine?: number
  newLine?: number
  content: string
}

type FileDetail = {
  name: string
  additions: number
  deletions: number
  diff: DiffLine[]
}

type VersionDetail = {
  id: number
  summary: string
  files: FileDetail[]
}

type TaskDetail = {
  versions: VersionDetail[]
}

type Task = {
  id: string
  title: string
  details: string
  status: "Completed" | "Open" | "Failed"
  versions?: number
  additions?: number
  deletions?: number
  taskDetails?: TaskDetail
}

export const tasks: Task[] = [
  {
    id: "1",
    title: "Make hello world label ominous",
    details: "8:15 PM · aideator/helloworld",
    status: "Completed",
    versions: 3,
    additions: 1,
    deletions: 1,
    taskDetails: {
      versions: [
        {
          id: 1,
          summary:
            "Updated the project description to read 'An ominous Hello World for Python,' making the greeting label more foreboding.",
          files: [
            {
              name: "README.md",
              additions: 1,
              deletions: 1,
              diff: [
                { type: "normal", oldLine: 1, newLine: 1, content: "# helloworld" },
                { type: "del", oldLine: 2, newLine: undefined, content: "- Hello World for Python" },
                { type: "add", oldLine: undefined, newLine: 2, content: "+ An ominous Hello World for Python" },
              ],
            },
          ],
        },
        {
          id: 2,
          summary: "A slightly different take, using 'Greetings, mortal' for a more dramatic flair.",
          files: [
            {
              name: "README.md",
              additions: 1,
              deletions: 1,
              diff: [
                { type: "normal", oldLine: 1, newLine: 1, content: "# helloworld" },
                { type: "del", oldLine: 2, newLine: undefined, content: "- Hello World for Python" },
                {
                  type: "add",
                  oldLine: undefined,
                  newLine: 2,
                  content: "+ Greetings, mortal. Welcome to the Python world.",
                },
              ],
            },
          ],
        },
        {
          id: 3,
          summary: "A more subtle change, adding an ellipsis to create a sense of suspense.",
          files: [
            {
              name: "README.md",
              additions: 1,
              deletions: 1,
              diff: [
                { type: "normal", oldLine: 1, newLine: 1, content: "# helloworld" },
                { type: "del", oldLine: 2, newLine: undefined, content: "- Hello World for Python" },
                { type: "add", oldLine: undefined, newLine: 2, content: "+ Hello World for Python..." },
              ],
            },
          ],
        },
      ],
    },
  },
  {
    id: "2",
    title: "Make hello world message cheerier",
    details: "7:29 PM · aideator/helloworld",
    status: "Completed",
    versions: 3,
    additions: 8,
    deletions: 8,
    taskDetails: {
      versions: [
        {
          id: 1,
          summary: "Added a cheerful greeting with exclamation marks and emojis.",
          files: [
            {
              name: "README.md",
              additions: 3,
              deletions: 3,
              diff: [
                { type: "normal", oldLine: 1, newLine: 1, content: "# helloworld" },
                { type: "del", oldLine: 2, newLine: undefined, content: "- Hello World for Python" },
                { type: "add", oldLine: undefined, newLine: 2, content: "+ Hello World for Python! 🎉✨" },
                { type: "normal", oldLine: 3, newLine: 3, content: "" },
                { type: "add", oldLine: undefined, newLine: 4, content: "+ Welcome to the most cheerful Python project!" },
              ],
            },
          ],
        },
        {
          id: 2,
          summary: "Made it even more cheerful with rainbow colors and celebration.",
          files: [
            {
              name: "README.md",
              additions: 4,
              deletions: 2,
              diff: [
                { type: "normal", oldLine: 1, newLine: 1, content: "# helloworld" },
                { type: "del", oldLine: 2, newLine: undefined, content: "- Hello World for Python" },
                { type: "add", oldLine: undefined, newLine: 2, content: "+ 🌈 SUPER HAPPY Hello World for Python! 🌈" },
                { type: "normal", oldLine: 3, newLine: 3, content: "" },
                { type: "add", oldLine: undefined, newLine: 4, content: "+ 🎊 The most joyful Python experience ever! 🎊" },
                { type: "add", oldLine: undefined, newLine: 5, content: "+ Let's code with happiness! 😊💖" },
              ],
            },
          ],
        },
        {
          id: 3,
          summary: "Toned it down to a warm, friendly welcome message.",
          files: [
            {
              name: "README.md",
              additions: 2,
              deletions: 3,
              diff: [
                { type: "normal", oldLine: 1, newLine: 1, content: "# helloworld" },
                { type: "del", oldLine: 2, newLine: undefined, content: "- Hello World for Python" },
                { type: "add", oldLine: undefined, newLine: 2, content: "+ A warm Hello World for Python 😊" },
                { type: "normal", oldLine: 3, newLine: 3, content: "" },
                { type: "add", oldLine: undefined, newLine: 4, content: "+ Hope you enjoy your Python journey!" },
              ],
            },
          ],
        },
      ],
    },
  },
  {
    id: "3",
    title: "Update hello world message",
    details: "Jul 9 · aideator/helloworld · 9iznu6-codex/update-hello-world-message",
    status: "Open",
  },
  {
    id: "4",
    title: "Update hello world message",
    details: "Jul 8 · aideator/helloworld",
    status: "Failed",
  },
  {
    id: "5",
    title: "Complete v2 UI functionality",
    details: "Jul 7 · heyalchang/dev-runner",
    status: "Completed",
    versions: 3,
    additions: 187,
    deletions: 7,
    taskDetails: {
      versions: [
        {
          id: 1,
          summary: "Implemented the new UI components.",
          files: [{ name: "components/ui/card.tsx", additions: 187, deletions: 7, diff: [] }],
        },
      ],
    },
  },
  {
    id: "6",
    title: "Complete v2 UI functionality",
    details: "Jul 7 · heyalchang/dev-runner",
    status: "Completed",
    versions: 3,
    additions: 0,
    deletions: 0,
    taskDetails: {
      versions: [
        {
          id: 1,
          summary: "Initial commit.",
          files: [],
        },
      ],
    },
  },
]
