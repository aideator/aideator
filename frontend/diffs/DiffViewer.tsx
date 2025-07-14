import React, { useEffect, useState } from "react";
import { DiffView, DiffModeEnum } from "@git-diff-view/react";
import { sampleMultiFileDiffData, type DiffData } from "./data";
import { 
  processMultiFileDiff,
  getDefaultOptions,
  type DiffViewOptions,
  type ProcessedDiffFile
} from "./utils";
import "@git-diff-view/react/styles/diff-view.css";

interface DiffViewerProps {
  data?: DiffData[];
  options?: DiffViewOptions;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ 
  data = sampleMultiFileDiffData.files,
  options = getDefaultOptions()
}) => {
  const [diffFiles, setDiffFiles] = useState<ProcessedDiffFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [collapsedFiles, setCollapsedFiles] = useState<Set<number>>(new Set());

  useEffect(() => {
    const loadDiff = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const processedFiles = await processMultiFileDiff({ files: data }, options);
        setDiffFiles(processedFiles);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load diff");
      } finally {
        setLoading(false);
      }
    };

    loadDiff();
  }, [data, options]);

  if (loading) {
    return (
      <div style={{ padding: "20px", textAlign: "center" }}>
        Loading diff...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "20px", color: "red" }}>
        Error: {error}
      </div>
    );
  }

  if (!diffFiles.length) {
    return null;
  }

  const toggleFileCollapse = (index: number) => {
    setCollapsedFiles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  return (
    <div style={{ height: "100%", overflow: "auto" }}>
      {diffFiles.map((file, index) => {
        const isCollapsed = collapsedFiles.has(index);
        return (
          <div key={index} style={{ marginBottom: index < diffFiles.length - 1 ? "40px" : 0 }}>
            <div style={{ 
              display: "flex",
              alignItems: "center",
              padding: "10px 20px", 
              backgroundColor: options.theme === "dark" ? "#1e1e1e" : "#f5f5f5",
              borderBottom: `1px solid ${options.theme === "dark" ? "#333" : "#ddd"}`,
              fontFamily: "monospace",
              fontSize: "14px",
              fontWeight: "bold"
            }}>
              <button
                onClick={() => toggleFileCollapse(index)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: "0 8px 0 0",
                  fontSize: "12px",
                  color: options.theme === "dark" ? "#aaa" : "#666"
                }}
              >
                {isCollapsed ? "▶" : "▼"}
              </button>
              <span style={{ flexGrow: 1 }}>{file.fileName}</span>
              <span style={{ 
                fontSize: "12px",
                fontWeight: "normal",
                marginLeft: "auto"
              }}>
                <span style={{ color: "#22c55e" }}>+{file.additions}</span>
                {" "}
                <span style={{ color: "#ef4444" }}>-{file.deletions}</span>
              </span>
            </div>
            {!isCollapsed && (
              <DiffView
                diffFile={file.diffFile}
                diffViewMode={options.mode === "unified" ? DiffModeEnum.Unified : DiffModeEnum.Split}
                diffViewWrap={options.wrap}
                diffViewHighlight={options.highlight}
                diffViewTheme={options.theme}
                diffViewFontSize={options.fontSize}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};