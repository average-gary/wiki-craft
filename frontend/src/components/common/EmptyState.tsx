import { FileText, Search, BookOpen, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

interface EmptyStateProps {
  icon?: 'documents' | 'search' | 'wiki' | 'upload';
  title: string;
  description: string;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
}

const icons = {
  documents: FileText,
  search: Search,
  wiki: BookOpen,
  upload: Upload,
};

export function EmptyState({ icon = 'documents', title, description, action }: EmptyStateProps) {
  const Icon = icons[icon];

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="rounded-full bg-muted p-4 mb-4">
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground max-w-sm mb-6">{description}</p>
      {action && (
        action.href ? (
          <Button asChild>
            <Link to={action.href}>{action.label}</Link>
          </Button>
        ) : (
          <Button onClick={action.onClick}>{action.label}</Button>
        )
      )}
    </div>
  );
}

export function NoDocuments() {
  return (
    <EmptyState
      icon="upload"
      title="No documents yet"
      description="Upload your first document to start building your knowledge base."
      action={{ label: 'Upload Document', href: '/documents' }}
    />
  );
}

export function NoSearchResults({ query }: { query: string }) {
  return (
    <EmptyState
      icon="search"
      title="No results found"
      description={`No matches found for "${query}". Try a different search term or upload more documents.`}
    />
  );
}

export function NoWikiContent() {
  return (
    <EmptyState
      icon="wiki"
      title="Generate your first wiki entry"
      description="Enter a topic or question above to generate a wiki entry from your knowledge base."
    />
  );
}
