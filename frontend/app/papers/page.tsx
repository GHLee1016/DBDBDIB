'use client'

import { useEffect, useState } from 'react'
import { getPaperAssignments, assignPapers, reassignPaper, PaperAssignment } from '@/lib/api'
import Badge from '@/components/ui/Badge'

const SEASON_ID = 1

export default function PapersPage() {
  const [assignments, setAssignments] = useState<PaperAssignment[]>([])
  const [loading, setLoading] = useState(true)
  const [assigning, setAssigning] = useState(false)
  const [reassigning, setReassigning] = useState<number | null>(null)
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  function load() {
    setLoading(true)
    getPaperAssignments(SEASON_ID)
      .then(setAssignments)
      .catch(() => setAssignments([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function handleAssignAll() {
    if (!confirm(`Season ${SEASON_ID} 합격자 전원에게 논문을 일괄 배정하시겠습니까?`)) return
    setAssigning(true)
    try {
      const res = await assignPapers(SEASON_ID) as { assigned_count: number; skipped_count: number }
      setMsg({ type: 'success', text: `배정 완료: ${res.assigned_count}명 | 미배정: ${res.skipped_count}명` })
      load()
    } catch (e: unknown) {
      setMsg({ type: 'error', text: e instanceof Error ? e.message : '오류 발생' })
    } finally {
      setAssigning(false)
    }
  }

  async function handleReassign(applicantId: number) {
    setReassigning(applicantId)
    try {
      await reassignPaper(applicantId)
      setMsg({ type: 'success', text: '논문 재배정 완료' })
      load()
    } catch (e: unknown) {
      setMsg({ type: 'error', text: e instanceof Error ? e.message : '오류 발생' })
    } finally {
      setReassigning(null)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-5">
        <h1 className="text-lg font-medium">논문 배정</h1>
        <button className="btn btn-primary" onClick={handleAssignAll} disabled={assigning}>
          {assigning ? '배정 중…' : `Season ${SEASON_ID} 일괄 배정`}
        </button>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2.5 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {msg.text}
          <button className="ml-3 opacity-60" onClick={() => setMsg(null)}>✕</button>
        </div>
      )}

      <div className="card">
        {loading ? (
          <p className="text-sm text-gray-400 py-8 text-center">불러오는 중…</p>
        ) : assignments.length === 0 ? (
          <p className="text-sm text-gray-400 py-8 text-center">배정된 논문이 없습니다.</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr>
                <th>지원자</th>
                <th>전공</th>
                <th>논문 제목</th>
                <th>카테고리</th>
                <th>난이도</th>
                <th>배정일</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {assignments.map((a) => (
                <tr key={a.applicant_id}>
                  <td className="font-medium">{a.name}</td>
                  <td className="text-gray-500">{a.major}</td>
                  <td className="text-xs max-w-[200px] truncate" title={a.paper_title}>{a.paper_title}</td>
                  <td className="text-gray-500 text-xs">{a.category}</td>
                  <td><Badge value={a.difficulty} /></td>
                  <td className="text-gray-400 text-xs">{a.assigned_at?.slice(0, 10)}</td>
                  <td>
                    <button
                      className="btn btn-sm"
                      onClick={() => handleReassign(a.applicant_id)}
                      disabled={reassigning === a.applicant_id}
                    >
                      {reassigning === a.applicant_id ? '…' : '재배정'}
                    </button>
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
