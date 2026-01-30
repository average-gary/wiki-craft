import { useState, FormEvent } from 'react';
import { Sparkles, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { useWikiTopics } from '@/hooks/useWiki';

interface WikiGeneratorProps {
  onGenerate: (query: string, maxSources: number, includeSources: boolean) => void;
  isLoading?: boolean;
}

export function WikiGenerator({ onGenerate, isLoading = false }: WikiGeneratorProps) {
  const [query, setQuery] = useState('');
  const [maxSources, setMaxSources] = useState('10');
  const [includeSources, setIncludeSources] = useState(true);

  const { data: topics } = useWikiTopics(10);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onGenerate(query.trim(), parseInt(maxSources), includeSources);
    }
  };

  const handleTopicClick = (topic: string) => {
    setQuery(topic);
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="query">Topic or Question</Label>
          <Input
            id="query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter a topic or question to generate a wiki entry..."
            disabled={isLoading}
            className="text-lg"
          />
        </div>

        <div className="flex flex-wrap items-end gap-4">
          <div className="space-y-2">
            <Label htmlFor="maxSources">Max Sources</Label>
            <Select value={maxSources} onValueChange={setMaxSources} disabled={isLoading}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="5">5</SelectItem>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="20">20</SelectItem>
                <SelectItem value="30">30</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2 pb-2">
            <Checkbox
              id="includeSources"
              checked={includeSources}
              onCheckedChange={(checked) => setIncludeSources(checked === true)}
              disabled={isLoading}
            />
            <Label htmlFor="includeSources" className="cursor-pointer">
              Include references
            </Label>
          </div>

          <div className="flex-1" />

          <Button type="submit" disabled={isLoading || !query.trim()} size="lg">
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Generate Wiki Entry
              </>
            )}
          </Button>
        </div>
      </form>

      {/* Suggested topics */}
      {topics?.topics && topics.topics.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">Suggested topics:</p>
          <div className="flex flex-wrap gap-2">
            {topics.topics.slice(0, 8).map((topic) => (
              <Badge
                key={topic}
                variant="secondary"
                className="cursor-pointer hover:bg-secondary/80"
                onClick={() => handleTopicClick(topic)}
              >
                {topic}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
