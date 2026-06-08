'use client'

import { useState } from 'react'
import { getApplicantStats, reassignPaper } from '@/lib/api'
import Badge from '@/components/ui/Badge'
import ScoreBar from '@/components/ui/ScoreBar'

const SEASON_ID = 12

type Applicant = {
  applicant_id: number
  name: string
  major: string
  final_status: string
  avg_score: number
  total_evals: number
  email?: string
}

type DetailData = {
  name: string
  avg_score: number
  total_evals: number
}

export default function ApplicantsPage() {
  const [applicants] = useState<Applicant[]>([])
  const [detail, setDetail] = useState<{ id: number; data: DetailData } | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [reassigning, setReassigning] = useState<number | null>(null)
  const [msg, setMsg] = useState('')

  async function loadDetail(id: number) {
    setDetailLoading(true)
    try {
      const data = await getApplicantStats(id)
      setDetail({ id, data })
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '오류 발생')
    } finally {
      setDetailLoading(false)
    }
  }

  async function handleReassign(id: number) {
    setReassigning(id)
    try {
      await reassignPaper(id)
      setMsg(`지원자 ${id} 논문 재배정 완료`)
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '오류 발생')
    } finally {
      setReassigning(null)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-5">
        <h1 className="text-lg font-medium">지원자 관리</h1>
        <span className="text-xs text-gray-400">Season {SEASON_ID}</span>
      </div>

      {msg && (
        <div className="mb-4 px-4 py-2.5 bg-blue-50 text-blue-700 rounded-lg text-sm">
          {msg}
          <button className="ml-3 text-blue-400 hover:text-blue-600" onClick={() => setMsg('')}>✕</button>
        </div>
      )}

      <div className="card">
        {applicants.length === 0 ? (
          <p className="text-sm text-gray-400 py-8 text-center">
            지원자 데이터를 불러오려면 API가 연결되어야 합니다.
          </p>
        ) : (
          <table className="w-full">
            <thead>
              <tr>
                <th>이름</th>
                <th>전공</th>
                <th>상태</th>
                <th className="w-36">평균 점수</th>
                <th>평가 횟수</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {applicants.map((a) => (
                <tr key={a.applicant_id}>
                  <td className="font-medium">{a.name}</td>
                  <td className="text-gray-500">{a.major}</td>
                  <td><Badge value={a.final_status} /></td>
                  <td><ScoreBar score={a.avg_score} /></td>
                  <td className="text-gray-500">{a.total_evals}회</td>
                  <td>
                    <div className="flex gap-1.5">
                      <button className="btn btn-sm" onClick={() => loadDetail(a.applicant_id)}>
                        {detailLoading && detail?.id === a.applicant_id ? '…' : '상세'}
                      </button>
                      <button
                        className="btn btn-sm"
                        onClick={() => handleReassign(a.applicant_id)}
                        disabled={a.final_status !== '합격'}
                      >
                        {reassigning === a.applicant_id ? '…' : '재배정'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {detail && (
        <div className="card mt-4">
          <div className="flex justify-between items-start mb-4">
            <p className="font-medium">{detail.data.name} — 상세</p>
            <button className="text-gray-400 hover:text-gray-600 text-sm" onClick={() => setDetail(null)}>✕</button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <p className="text-xs text-gray-500 mb-1">평균 점수</p>
              <p className="text-2xl font-medium">{detail.data.avg_score.toFixed(1)}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <p className="text-xs text-gray-500 mb-1">평가 횟수</p>
              <p className="text-2xl font-medium">{detail.data.total_evals}회</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
