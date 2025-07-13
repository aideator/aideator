import { DiffFile, generateDiffFile } from "@git-diff-view/file";
import { DiffFile as CoreDiffFile } from "@git-diff-view/core";
import type { DiffData, MultiFileDiffData } from "./data";

export interface DiffViewOptions {
  mode?: "split" | "unified";
  highlight?: boolean;
  wrap?: boolean;
  theme?: "light" | "dark";
  fontSize?: number;
}

export function createDiffFileFromContent(data: DiffData): DiffFile {
  const diffFile = generateDiffFile(
    data.oldFile.fileName || "old-file",
    data.oldFile.content || "",
    data.newFile.fileName || "new-file", 
    data.newFile.content || "",
    data.oldFile.fileLang || "",
    data.newFile.fileLang || ""
  );
  
  return diffFile;
}

export function createDiffFileFromHunks(data: DiffData): CoreDiffFile {
  if (!data.hunks) {
    throw new Error("Hunks data is required for git diff mode");
  }
  
  const diffFile = new CoreDiffFile(
    data.oldFile.fileName || "",
    data.oldFile.content || "",
    data.newFile.fileName || "",
    data.newFile.content || "",
    data.hunks,
    data.oldFile.fileLang || "",
    data.newFile.fileLang || ""
  );
  
  return diffFile;
}

export async function initializeDiffFile(
  diffFile: DiffFile | CoreDiffFile,
  options: DiffViewOptions = {}
): Promise<void> {
  diffFile.initTheme(options.theme || "light");
  await diffFile.init();
  diffFile.buildSplitDiffLines();
  diffFile.buildUnifiedDiffLines();
}

export function getDefaultOptions(): DiffViewOptions {
  return {
    mode: "split",
    highlight: true,
    wrap: false,
    theme: "light",
    fontSize: 13
  };
}

export interface ProcessedDiffFile {
  diffFile: DiffFile | CoreDiffFile;
  fileName: string;
  isGitDiff: boolean;
  additions: number;
  deletions: number;
}

function countLineChanges(diffFile: DiffFile | CoreDiffFile): { additions: number; deletions: number } {
  // DiffFile instances have built-in properties for addition and deletion counts
  return {
    additions: diffFile.additionLength || 0,
    deletions: diffFile.deletionLength || 0
  };
}

export async function processMultiFileDiff(
  data: MultiFileDiffData,
  options: DiffViewOptions = {}
): Promise<ProcessedDiffFile[]> {
  const processedFiles: ProcessedDiffFile[] = [];

  for (const fileData of data.files) {
    const isGitDiff = !!fileData.hunks;
    const diffFile = isGitDiff
      ? createDiffFileFromHunks(fileData)
      : createDiffFileFromContent(fileData);
    
    await initializeDiffFile(diffFile, options);
    
    const { additions, deletions } = countLineChanges(diffFile);
    
    processedFiles.push({
      diffFile,
      fileName: fileData.newFile.fileName || fileData.oldFile.fileName || "unnamed",
      isGitDiff,
      additions,
      deletions
    });
  }

  return processedFiles;
}