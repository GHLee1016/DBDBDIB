'use client'

import { useEffect, useState } from 'react'
import { getSeasonPassRate, getPapersWithCitations, SeasonStat, PaperStat } from '@/lib/api'
import Badge from '@/components/ui/Badge'

const SEASON_ID = 12

export default function StatsPage() {
  const [seasons, setSeasons] = useState<SeasonStat[]>([])
  const [papers, setPapers] = useState<PaperStat[]>([])
  const [loadingSeasons, setLoadingSeasons] = useState(true)
  const [loadingPapers, setLoadingPapers] = useState(false)
  const [papersLoaded, setPapersLoaded] = useState(false)
  const [papersMeta, setPapersMeta] = useState<{ total: number; adjusted: number } | null>(null)

  useEffect(() => {
    getSeasonPassRate()
      .then((res) => setSeasons(res.season_ranking))
      .catch(() => setSeasons([]))
      .finally(() => setLoadingSeasons(false))
  }, [])

  async function loadPapers() {
    setLoadingPapers(true)
    try {
      const res = await getPapersWithCitations(SEASON_ID)
      setPapers(res.paper_ranking)
      setPapersMeta({ total: res.total_papers, adjusted: res.difficulty_adjusted })
      setPapersLoaded(true)
    } catch {
      setPapers([])
    } finally {
      setLoadingPapers(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">통계</h1>

      <div className="card mb-5">
        <p className="text-sm font-medium mb-4">기수별 합격률 랭킹 (Google Sheets 기반)</p>
        {loadingSeasons ? (
          <p className="text-sm text-gray-400 py-4 text-center">불러오는 중…</p>
        ) : seasons.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center">데이터 없음</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr>
                <th>순위</th>
                <th>기수</th>
                <th>총 지원</th>
                <th>합격</th>
                <th>합격률</th>
                <th>평균 점수</th>
                <th>출처</th>
              </tr>
            </thead>
            <tbody>
              {seasons.map((s) => (
                <tr key={s.season_id}>
                  <td className="font-medium text-gray-500">#{s.rank}</td>
                  <td className="font-medium">{s.season_name}</td>
                  <td className="text-gray-500">{s.total}명</td>
                  <td className="text-gray-500">{s.passed}명</td>
                  <td>
                    <span className="font-medium text-green-600">{s.pass_rate.toFixed(1)}%</span>
                  </td>
                  <td className="text-gray-500">
                    {s.avg_score != null ? `${s.avg_score.toFixed(1)}점` : '—'}
                  </td>
                  <td className="text-xs text-gray-400">{s.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <div>
            <p className="text-sm font-medium">논문 인용수 기반 난이도 보정</p>
            {papersMeta && (
              <p className="text-xs text-gray-400 mt-0.5">
                총 {papersMeta.total}편 · 난이도 보정 {papersMeta.adjusted}편
              </p>
            )}
          </div>
          {!papersLoaded && (
            <button className="btn btn-sm" onClick={loadPapers} disabled={loadingPapers}>
              {loadingPapers ? '조회 중… (시간 소요)' : 'Season 12 조회'}
            </button>
          )}
        </div>

        {loadingPapers && (
          <div className="py-6 text-center">
            <p className="text-sm text-gray-500">Semantic Scholar API 호출 중…</p>
            <p className="text-xs text-gray-400 mt-1">논문당 약 1초 소요됩니다.</p>
          </div>
        )}

        {!loadingPapers && !papersLoaded && (
          <p className="text-sm text-gray-400 py-4 text-center">
            &quot;Season 12 조회&quot; 버튼을 눌러 인용수를 가져오세요.
          </p>
        )}

        {papersLoaded && papers.length === 0 && (
          <p className="text-sm text-gray-400 py-4 text-center">데이터 없음</p>
        )}

        {papersLoaded && papers.length > 0 && (
          <table className="w-full">
            <thead>
              <tr>
                <th>순위</th>
                <th>논문 제목</th>
                <th>인용수</th>
                <th>원래 난이도</th>
                <th>보정 난이도</th>
                <th>배정 대상</th>
              </tr>
            </thead>
            <tbody>
              {papers.map((p) => (
                <tr key={p.paper_id}>
                  <td className="text-gray-400">#{p.rank}</td>
                  <td className="text-xs max-w-[200px]" title={p.title}>{p.title}</td>
                  <td className="font-medium">{p.citation_count?.toLocaleString() ?? '—'}</td>
                  <td><Badge value={p.original_difficulty} /></td>
                  <td>
                    <span className={p.difficulty_changed ? 'font-medium' : ''}>
                      <Badge value={p.adjusted_difficulty} />
                      {p.difficulty_changed && <span className="ml-1 text-xs text-amber-500">↑</span>}
                    </span>
                  </td>
                  <td className="text-gray-500 text-xs">{p.assigned_to ?? '미배정'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
