'use client'

import { useEffect, useState } from 'react'
import { getSeasonPassRate, SeasonStat } from '@/lib/api'

export default function DashboardPage() {
  const [stats, setStats] = useState<SeasonStat | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSeasonPassRate()
      .then((res) => setStats(res.season_ranking[0] ?? null))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const current = stats

  return (
    <div>
      <h1 className="page-title">대시보드</h1>

      <div className="grid grid-cols-4 gap-3 mb-5">
        {[
          { label: '총 지원자', value: loading ? '…' : current?.total ?? 0, color: '' },
          { label: '합격', value: loading ? '…' : current?.passed ?? 0, color: 'text-green-600' },
          { label: '불합격', value: loading ? '…' : current?.failed ?? 0, color: 'text-red-600' },
          { label: '검토중', value: loading ? '…' : current?.pending ?? 0, color: 'text-amber-600' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-gray-100 rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 mb-1">{label}</p>
            <p className={`text-2xl font-medium ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <p className="text-sm font-medium mb-4">현재 시즌</p>
          {loading ? (
            <p className="text-sm text-gray-400">불러오는 중…</p>
          ) : current ? (
            <div className="space-y-2">
              {[
                { label: '시즌명', value: current.season_name },
                { label: '합격률', value: `${current.pass_rate.toFixed(1)}%` },
                { label: '평균 점수', value: current.avg_score ? `${current.avg_score.toFixed(1)}점` : '—' },
                { label: '데이터 출처', value: current.source },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between text-sm py-1.5 border-b border-gray-100 last:border-0">
                  <span className="text-gray-500">{label}</span>
                  <span className="font-medium">{value}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">시즌 데이터 없음</p>
          )}
        </div>

        <div className="card">
          <p className="text-sm font-medium mb-4">전공별 합격 분포</p>
          {loading ? (
            <p className="text-sm text-gray-400">불러오는 중…</p>
          ) : current?.major_distribution && Object.keys(current.major_distribution).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(current.major_distribution).map(([major, count]) => (
                <div key={major} className="flex items-center gap-2 text-sm">
                  <span className="text-gray-500 w-24 shrink-0 truncate">{major}</span>
                  <div className="flex-1 h-1 bg-gray-100 rounded-full">
                    <div className="h-full bg-blue-400 rounded-full" style={{ width: `${(count / (current.passed || 1)) * 100}%` }} />
                  </div>
                  <span className="text-xs text-gray-400 w-4 text-right">{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">데이터 없음</p>
          )}
        </div>
      </div>
    </div>
  )
}
