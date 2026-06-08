'use client'

import { useEffect, useState } from 'react'
import { listApplicants, reassignPaper, Applicant } from '@/lib/api'

const SEASON_ID = 12

const STATUS_COLORS: Record<string, string> = {
  '합격':   'badge badge-pass',
  '불합격': 'badge badge-fail',
  '진행중': 'badge badge-warning',
  '대기':   'badge badge-info',
}

export default function ApplicantsPage() {
  const [applicants, setApplicants] = useState<Applicant[]>([])
  const [loading, setLoading]       = useState(true)
  const [search, setSearch]         = useState('')
  const [statusFilter, setStatusFilter] = useState('전체')
  const [reassigning, setReassigning]   = useState<number | null>(null)
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  function load() {
    setLoading(true)
    listApplicants(SEASON_ID)
      .then(setApplicants)
      .catch(() => setApplicants([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function handleReassign(id: number) {
    if (!confirm('이 지원자의 논문을 자동 재배정하시겠습니까?')) return
    setReassigning(id)
    try {
      const res = await reassignPaper(id) as { new_paper: string }
      setMsg({ type: 'success', text: `재배정 완료: ${res.new_paper}` })
      load()
    } catch (e: unknown) {
      setMsg({ type: 'error', text: e instanceof Error ? e.message : '오류 발생' })
    } finally {
      setReassigning(null)
    }
  }

  const statuses = ['전체', '합격', '불합격', '진행중', '대기']
  const filtered = applicants.filter(a => {
    const matchSearch = a.name.includes(search) || a.major.includes(search) || (a.email ?? '').includes(search)
    const matchStatus = statusFilter === '전체' || a.final_status === statusFilter
    return matchSearch && matchStatus
  })

  return (
    <div>
      <div className="flex justify-between items-center mb-5">
        <h1 className="page-title">지원자 관리</h1>
        <span className="text-sm text-gray-400">Season {SEASON_ID} · {applicants.length}명</span>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2.5 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {msg.text}
          <button className="ml-3 opacity-60" onClick={() => setMsg(null)}>✕</button>
        </div>
      )}

      <div className="flex gap-3 mb-4">
        <input
          className="form-input flex-1"
          placeholder="이름, 전공, 이메일 검색"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <div className="flex gap-1">
          {statuses.map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                statusFilter === s
                  ? 'bg-gray-900 text-white'
                  : 'bg-white border border-gray-200 text-gray-500 hover:bg-gray-50'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        {loading ? (
          <p className="text-sm text-gray-400 py-12 text-center">불러오는 중…</p>
        ) : filtered.length === 0 ? (
          <p className="text-sm text-gray-400 py-12 text-center">지원자가 없습니다.</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr>
                <th>이름</th>
                <th>전공</th>
                <th>이메일</th>
                <th>상태</th>
                <th>평균 점수</th>
                <th>평가 수</th>
                <th>배정 논문</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(a => (
                <tr key={a.applicant_id}>
                  <td className="font-medium">{a.name}</td>
                  <td className="text-gray-500 text-sm">{a.major}</td>
                  <td className="text-gray-400 text-xs">{a.email}</td>
                  <td>
                    <span className={STATUS_COLORS[a.final_status] ?? 'badge badge-info'}>
                      {a.final_status}
                    </span>
                  </td>
                  <td className="text-center">
                    {a.avg_score != null ? (
                      <span className={`font-medium ${Number(a.avg_score) >= 80 ? 'text-green-600' : 'text-red-500'}`}>
                        {Number(a.avg_score).toFixed(1)}
                      </span>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="text-center text-gray-500">{a.total_evals}</td>
                  <td className="text-xs text-gray-500 max-w-[180px] truncate" title={a.paper_title ?? ''}>
                    {a.paper_title ?? <span className="text-gray-300">미배정</span>}
                  </td>
                  <td>
                    {a.final_status === '합격' && (
                      <button
                        className="btn btn-sm"
                        onClick={() => handleReassign(a.applicant_id)}
                        disabled={reassigning === a.applicant_id}
                      >
                        {reassigning === a.applicant_id ? '…' : '논문 재배정'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
