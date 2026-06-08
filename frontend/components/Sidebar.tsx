'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const NAV = [
  { href: '/dashboard',    icon: '⊞', label: '대시보드' },
  { href: '/applicants',   icon: '👥', label: '지원자' },
  { href: '/documents',    icon: '📄', label: '서류' },
  { href: '/evaluations',  icon: '✏️', label: '평가' },
  { href: '/papers',       icon: '📚', label: '논문 배정' },
  { href: '/disqualified', icon: '🚫', label: '결격자' },
  { href: '/season',       icon: '📅', label: '시즌 관리' },
  { href: '/stats',        icon: '📊', label: '통계' },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-48 shrink-0 bg-gray-50 border-r border-gray-200 flex flex-col">
      <div className="px-4 py-4 border-b border-gray-200">
        <h1 className="text-sm font-medium text-gray-900">디비디비딥</h1>
        <p className="text-xs text-gray-400 mt-0.5">12기 어드민</p>
      </div>
      <nav className="flex-1 py-2">
        {NAV.map(({ href, icon, label }) => {
          const active = pathname === href || pathname.startsWith(href + '/')
          return (
            <Link
              key={href}
              href={href}
              className={[
                'flex items-center gap-2.5 px-4 py-2 text-sm transition-colors',
                active
                  ? 'bg-white text-gray-900 font-medium border-r-2 border-gray-900'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100',
              ].join(' ')}
            >
              <span className="text-base leading-none">{icon}</span>
              {label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
