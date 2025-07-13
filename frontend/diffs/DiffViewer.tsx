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

  const showFileHeaders = diffFiles.length > 1;

  return (
    <div style={{ height: "100%", overflow: "auto" }}>
      {diffFiles.map((file, index) => (
        <div key={index} style={{ marginBottom: index < diffFiles.length - 1 ? "40px" : 0 }}>
          {showFileHeaders && (
            <div style={{ 
              padding: "10px 20px", 
              backgroundColor: options.theme === "dark" ? "#1e1e1e" : "#f5f5f5",
              borderBottom: `1px solid ${options.theme === "dark" ? "#333" : "#ddd"}`,
              fontFamily: "monospace",
              fontSize: "14px",
              fontWeight: "bold"
            }}>
              {file.fileName}
            </div>
          )}
          <DiffView
            diffFile={file.diffFile}
            diffViewMode={options.mode === "unified" ? DiffModeEnum.Unified : DiffModeEnum.Split}
            diffViewWrap={options.wrap}
            diffViewHighlight={options.highlight}
            diffViewTheme={options.theme}
            diffViewFontSize={options.fontSize}
          />
        </div>
      ))}
    </div>
  );
};