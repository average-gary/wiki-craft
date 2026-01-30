import { useState } from 'react';
import { useDocuments, useDeleteDocument } from '@/hooks/useDocuments';
import { DocumentCard } from './DocumentCard';
import { DocumentCardSkeleton } from '@/components/common/LoadingState';
import { NoDocuments } from '@/components/common/EmptyState';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { DocumentDetail } from './DocumentDetail';

export function DocumentList() {
  const { data, isLoading, error } = useDocuments();
  const deleteMutation = useDeleteDocument();
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id);
  };

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <DocumentCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-destructive">
        Failed to load documents: {error.message}
      </div>
    );
  }

  if (!data?.documents.length) {
    return <NoDocuments />;
  }

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.documents.map((doc) => (
          <DocumentCard
            key={doc.document_id}
            document={doc}
            onDelete={handleDelete}
            onView={setSelectedDocId}
            isDeleting={deleteMutation.isPending}
          />
        ))}
      </div>

      <Dialog open={!!selectedDocId} onOpenChange={() => setSelectedDocId(null)}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Document Details</DialogTitle>
          </DialogHeader>
          {selectedDocId && <DocumentDetail documentId={selectedDocId} />}
        </DialogContent>
      </Dialog>
    </>
  );
}
