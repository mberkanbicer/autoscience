'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/' },
  { name: 'Projects', href: '/projects' },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-gray-900 text-white">
      <div className="p-4">
        <Link href="/" className="text-xl font-bold">
          Autoscience
        </Link>
        <p className="text-sm text-gray-400 mt-1">Research Cognition System</p>
      </div>

      <nav className="mt-8">
        {navigation.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              'block px-4 py-3 text-sm font-medium transition-colors',
              pathname === item.href
                ? 'bg-gray-800 text-white'
                : 'text-gray-300 hover:bg-gray-800 hover:text-white'
            )}
          >
            {item.name}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
