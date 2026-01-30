import { Link, useLocation } from 'react-router-dom';
import { Menu, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import { cn } from '@/lib/utils';

interface HeaderProps {
  onMenuClick: () => void;
}

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/documents', label: 'Documents' },
  { path: '/search', label: 'Search' },
  { path: '/wiki', label: 'Wiki' },
];

export function Header({ onMenuClick }: HeaderProps) {
  const location = useLocation();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4 md:px-6">
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden mr-2"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 mr-6">
          <div className="bg-primary text-primary-foreground rounded p-1">
            <BookOpen className="h-5 w-5" />
          </div>
          <span className="font-bold text-lg hidden sm:inline">Wiki-Craft</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-1 flex-1">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'px-3 py-2 text-sm font-medium rounded-md transition-colors',
                location.pathname === item.path
                  ? 'bg-secondary text-secondary-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Right side actions */}
        <div className="flex items-center gap-2 ml-auto">
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
