import { Trash2, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { getDocumentTypeIcon, formatRelativeTime } from '@/lib/utils';
import type { DocumentInfo } from '@/types/api';

interface DocumentCardProps {
  document: DocumentInfo;
  onDelete: (id: string) => void;
  onView: (id: string) => void;
  isDeleting?: boolean;
}

export function DocumentCard({ document, onDelete, onView, isDeleting }: DocumentCardProps) {
  const icon = getDocumentTypeIcon(document.document_type);

  return (
    <div className="group rounded-lg border bg-card p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="text-2xl">{icon}</div>
        <div className="flex-1 min-w-0">
          <h3 className="font-medium truncate">
            {document.document_title || document.source_path.split('/').pop()}
          </h3>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <Badge variant="secondary" className="text-xs">
              {document.document_type.toUpperCase()}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {document.total_chunks} chunks
            </span>
            <span className="text-xs text-muted-foreground">
              {formatRelativeTime(document.ingested_at)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onView(document.document_id)}
            title="View document"
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                disabled={isDeleting}
                title="Delete document"
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Document</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete "{document.document_title || document.source_path}"?
                  This will remove all {document.total_chunks} chunks from the knowledge base.
                  This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => onDelete(document.document_id)}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </div>
  );
}
