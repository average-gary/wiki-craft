import { Link } from 'react-router-dom';
import { FileText, Search, BookOpen, Upload, Database, Layers } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useStats } from '@/hooks/useStats';
import { useDocuments } from '@/hooks/useDocuments';
import { StatCardSkeleton, DocumentCardSkeleton } from '@/components/common/LoadingState';
import { DocumentCard } from '@/components/documents/DocumentCard';
import { useDeleteDocument } from '@/hooks/useDocuments';

export function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useStats();
  const { data: docs, isLoading: docsLoading } = useDocuments(0, 5);
  const deleteMutation = useDeleteDocument();

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Welcome to Wiki-Craft. Manage your knowledge base and generate wiki content.
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statsLoading ? (
          <>
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </>
        ) : (
          <>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Documents</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_documents || 0}</div>
                <p className="text-xs text-muted-foreground">
                  Indexed documents
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Chunks</CardTitle>
                <Layers className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_chunks || 0}</div>
                <p className="text-xs text-muted-foreground">
                  Searchable chunks
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg. Chunks</CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.avg_chunks_per_document?.toFixed(1) || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Per document
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">File Types</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.documents_by_type
                    ? Object.keys(stats.documents_by_type).length
                    : 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Document types
                </p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Link to="/documents">
            <Card className="cursor-pointer hover:shadow-md transition-shadow">
              <CardContent className="flex items-center gap-4 p-6">
                <div className="rounded-full bg-primary/10 p-3">
                  <Upload className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">Upload Document</h3>
                  <p className="text-sm text-muted-foreground">Add to knowledge base</p>
                </div>
              </CardContent>
            </Card>
          </Link>
          <Link to="/search">
            <Card className="cursor-pointer hover:shadow-md transition-shadow">
              <CardContent className="flex items-center gap-4 p-6">
                <div className="rounded-full bg-primary/10 p-3">
                  <Search className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">Search Knowledge</h3>
                  <p className="text-sm text-muted-foreground">Find information</p>
                </div>
              </CardContent>
            </Card>
          </Link>
          <Link to="/wiki">
            <Card className="cursor-pointer hover:shadow-md transition-shadow">
              <CardContent className="flex items-center gap-4 p-6">
                <div className="rounded-full bg-primary/10 p-3">
                  <BookOpen className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">Generate Wiki</h3>
                  <p className="text-sm text-muted-foreground">Create wiki entry</p>
                </div>
              </CardContent>
            </Card>
          </Link>
          <Link to="/documents">
            <Card className="cursor-pointer hover:shadow-md transition-shadow">
              <CardContent className="flex items-center gap-4 p-6">
                <div className="rounded-full bg-primary/10 p-3">
                  <FileText className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">View Documents</h3>
                  <p className="text-sm text-muted-foreground">Manage your files</p>
                </div>
              </CardContent>
            </Card>
          </Link>
        </div>
      </div>

      {/* Recent Documents */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Recent Documents</h2>
          <Button variant="outline" asChild>
            <Link to="/documents">View All</Link>
          </Button>
        </div>
        {docsLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <DocumentCardSkeleton />
            <DocumentCardSkeleton />
            <DocumentCardSkeleton />
          </div>
        ) : docs?.documents.length ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {docs.documents.slice(0, 6).map((doc) => (
              <DocumentCard
                key={doc.document_id}
                document={doc}
                onDelete={(id) => deleteMutation.mutate(id)}
                onView={() => {}}
                isDeleting={deleteMutation.isPending}
              />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <FileText className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No documents yet</h3>
              <p className="text-muted-foreground mb-4">
                Upload your first document to get started
              </p>
              <Button asChild>
                <Link to="/documents">Upload Document</Link>
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
