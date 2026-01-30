import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUploadDocuments } from '@/hooks/useDocuments';
import { cn } from '@/lib/utils';
import type { IngestResponse } from '@/types/api';

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'text/markdown': ['.md'],
  'text/plain': ['.txt'],
  'text/html': ['.html', '.htm'],
  'application/epub+zip': ['.epub'],
};

interface UploadResult {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  result?: IngestResponse;
  error?: string;
}

export function UploadZone() {
  const [files, setFiles] = useState<UploadResult[]>([]);
  const uploadMutation = useUploadDocuments();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadResult[] = acceptedFiles.map(file => ({
      file,
      status: 'pending',
    }));
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    multiple: true,
  });

  const handleUpload = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    if (pendingFiles.length === 0) return;

    // Mark all as uploading
    setFiles(prev =>
      prev.map(f =>
        f.status === 'pending' ? { ...f, status: 'uploading' } : f
      )
    );

    try {
      const results = await uploadMutation.mutateAsync(
        pendingFiles.map(f => f.file)
      );

      // Update with results
      setFiles(prev =>
        prev.map(f => {
          if (f.status !== 'uploading') return f;
          const result = results.find(r => r.filename === f.file.name);
          if (result) {
            return {
              ...f,
              status: result.status === 'success' ? 'success' : 'error',
              result,
              error: result.errors?.join(', '),
            };
          }
          return { ...f, status: 'error', error: 'Unknown error' };
        })
      );
    } catch (error) {
      setFiles(prev =>
        prev.map(f =>
          f.status === 'uploading'
            ? { ...f, status: 'error', error: String(error) }
            : f
        )
      );
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearCompleted = () => {
    setFiles(prev => prev.filter(f => f.status === 'pending' || f.status === 'uploading'));
  };

  const pendingCount = files.filter(f => f.status === 'pending').length;
  const successCount = files.filter(f => f.status === 'success').length;

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-primary/50'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="h-10 w-10 mx-auto mb-4 text-muted-foreground" />
        {isDragActive ? (
          <p className="text-primary font-medium">Drop files here...</p>
        ) : (
          <>
            <p className="font-medium mb-1">Drag and drop files here</p>
            <p className="text-sm text-muted-foreground">
              or click to browse
            </p>
          </>
        )}
        <p className="text-xs text-muted-foreground mt-4">
          Supported: PDF, DOCX, XLSX, MD, TXT, HTML, EPUB
        </p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">
              {files.length} file{files.length !== 1 ? 's' : ''} selected
            </p>
            {successCount > 0 && (
              <Button variant="ghost" size="sm" onClick={clearCompleted}>
                Clear completed
              </Button>
            )}
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {files.map((item, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-3 rounded-lg border bg-card"
              >
                <File className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{item.file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(item.file.size / 1024).toFixed(1)} KB
                    {item.result && ` • ${item.result.chunks_created} chunks`}
                  </p>
                </div>
                <div className="flex-shrink-0">
                  {item.status === 'pending' && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeFile(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                  {item.status === 'uploading' && (
                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  )}
                  {item.status === 'success' && (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                  {item.status === 'error' && (
                    <span title={item.error}>
                      <AlertCircle className="h-5 w-5 text-destructive" />
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {pendingCount > 0 && (
            <Button
              onClick={handleUpload}
              disabled={uploadMutation.isPending}
              className="w-full"
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload {pendingCount} file{pendingCount !== 1 ? 's' : ''}
                </>
              )}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
