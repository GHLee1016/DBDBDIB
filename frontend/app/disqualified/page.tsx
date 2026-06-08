'use client'

import { useEffect, useState } from 'react'
import { getDisqualifiedList, DisqualifiedApplicant } from '@/lib/api'

const SEASON_ID = 12

export default function DisqualifiedPage() {
  const [list, setList] = useState<DisqualifiedApplicant[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDisqualifiedList(SEASON_ID)
      .then(setList)
      .catch(() => setList([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <h1 className="page-title">결격자 목록</h1>

      <div className="card">
        {loading ? (
          <p className="text-sm text-gray-400 py-8 text-center">불러오는 중…</p>
        ) : list.length === 0 ? (
          <p className="text-sm text-gray-400 py-8 text-center">결격자가 없습니다.</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr>
                <th>이름</th>
                <th>전공</th>
                <th>서류 유형</th>
                <th>사유</th>
              </tr>
            </thead>
            <tbody>
              {list.map((d, i) => (
                <tr key={i}>
                  <td className="font-medium">{d.name}</td>
                  <td className="text-gray-500">{d.major}</td>
                  <td className="text-gray-500">{d.doc_type}</td>
                  <td className="text-gray-500 text-xs">{d.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <p className="text-xs text-gray-400 mt-3">
        결격 처리는 서류 관리 페이지에서 수행할 수 있습니다.
      </p>
    </div>
  )
}
