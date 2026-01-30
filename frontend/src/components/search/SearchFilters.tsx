import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import type { DocumentType } from '@/types/api';

const DOCUMENT_TYPES: { value: DocumentType; label: string }[] = [
  { value: 'pdf', label: 'PDF' },
  { value: 'docx', label: 'Word' },
  { value: 'xlsx', label: 'Excel' },
  { value: 'markdown', label: 'Markdown' },
  { value: 'html', label: 'HTML' },
  { value: 'epub', label: 'EPUB' },
  { value: 'text', label: 'Text' },
];

interface SearchFiltersProps {
  selectedTypes: DocumentType[];
  onTypesChange: (types: DocumentType[]) => void;
}

export function SearchFilters({ selectedTypes, onTypesChange }: SearchFiltersProps) {
  const toggleType = (type: DocumentType) => {
    if (selectedTypes.includes(type)) {
      onTypesChange(selectedTypes.filter(t => t !== type));
    } else {
      onTypesChange([...selectedTypes, type]);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-4">
      <span className="text-sm font-medium">Filter:</span>
      {DOCUMENT_TYPES.map(({ value, label }) => (
        <div key={value} className="flex items-center space-x-2">
          <Checkbox
            id={`type-${value}`}
            checked={selectedTypes.includes(value)}
            onCheckedChange={() => toggleType(value)}
          />
          <Label
            htmlFor={`type-${value}`}
            className="text-sm cursor-pointer"
          >
            {label}
          </Label>
        </div>
      ))}
    </div>
  );
}
