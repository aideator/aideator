"use client";

import React, { useEffect, useState, useMemo } from "react";
import { DiffView, DiffModeEnum } from "@git-diff-view/react";
import { sampleDiffData, sampleGitDiffData } from "./data";
import { 
  createDiffFileFromContent, 
  createDiffFileFromHunks, 
  initializeDiffFile,
  getDefaultOptions,
  type DiffViewOptions 
} from "./utils";
import "@git-diff-view/react/styles/diff-view.css";

interface DiffViewerProps {
  options?: DiffViewOptions;
  useGitDiff?: boolean;
}

const defaultOptions = getDefaultOptions();

export const DiffViewer: React.FC<DiffViewerProps> = ({ 
  options: providedOptions,
  useGitDiff = false 
}) => {
  const options = useMemo(() => providedOptions || defaultOptions, [providedOptions]);
  
  console.log('DiffViewer rendering, useGitDiff:', useGitDiff, 'options:', options);
  const [diffFile, setDiffFile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDiff = async () => {
      console.log('loadDiff starting');
      try {
        setLoading(true);
        setError(null);
        
        const data = useGitDiff ? sampleGitDiffData : sampleDiffData;
        console.log('Using data:', data);
        
        const file = useGitDiff 
          ? createDiffFileFromHunks(data)
          : createDiffFileFromContent(data);
        console.log('Created file:', file);
        
        console.log('Initializing diff file...');
        await initializeDiffFile(file, options);
        console.log('Diff file initialized:', file);
        setDiffFile(file);
      } catch (err) {
        console.error('Error loading diff:', err);
        setError(err instanceof Error ? err.message : "Failed to load diff");
      } finally {
        console.log('loadDiff complete, setting loading to false');
        setLoading(false);
      }
    };

    loadDiff();
  }, [useGitDiff, options]);

  if (error) {
    return (
      <div style={{ padding: "20px", color: "red" }}>
        Error: {error}
      </div>
    );
  }


  if (loading) {
    console.log('Still loading, showing loading message');
    return (
      <div style={{ padding: "20px", textAlign: "center" }}>
        Loading diff...
      </div>
    );
  }

  if (!diffFile) {
    console.log('No diffFile, returning null');
    return null;
  }
  
  console.log('Rendering DiffView with diffFile:', diffFile);

  return (
    <div style={{ height: "100%", overflow: "auto" }}>
      <DiffView
        diffFile={diffFile}
        diffViewMode={options.mode === "unified" ? DiffModeEnum.Unified : DiffModeEnum.Split}
        diffViewWrap={options.wrap}
        diffViewHighlight={options.highlight}
        diffViewTheme={options.theme}
        diffViewFontSize={options.fontSize}
      />
    </div>
  );
};