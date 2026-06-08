'use client'

import { useState } from 'react'
import { updateDocument } from '@/lib/api'
import Badge from '@/components/ui/Badge'

const ALLOWED_STATUSES = ['pending', 'verified', 'missing', 'incomplete']

type DocEditState = {
  doc_id: number
  applicant_name: string
  status: string
  is_disqualified: boolean
  issue_note: string
}

export default function DocumentsPage() {
  const [editing, setEditing] = useState<DocEditState | null>(null)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  async function handleSave() {
    if (!editing) return
    setSaving(true)
    try {
      await updateDocument(editing.doc_id, {
        status: editing.status,
        is_disqualified: editing.is_disqualified,
        issue_note: editing.issue_note,
      })
      setMsg(`${editing.applicant_name} 서류 상태 저장 완료`)
      setEditing(null)
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '저장 실패')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">서류 관리</h1>

      {msg && (
        <div className="mb-4 px-4 py-2.5 bg-blue-50 text-blue-700 rounded-lg text-sm">
          {msg}
          <button className="ml-3 text-blue-400" onClick={() => setMsg('')}>✕</button>
        </div>
      )}

      <div className="card">
        <p className="text-sm text-gray-400 py-8 text-center">
          서류 데이터를 불러오려면 API가 연결되어야 합니다.
          <br />
          <span className="text-xs">doc_id로 수정 폼을 직접 열 수 있습니다.</span>
        </p>
      </div>

      <div className="card mt-4">
        <p className="text-sm font-medium mb-4">서류 직접 수정</p>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="form-label">Doc ID</label>
            <input
              type="number"
              className="form-input"
              placeholder="서류 ID 입력"
              onChange={(e) => setEditing(prev => prev
                ? { ...prev, doc_id: Number(e.target.value) }
                : { doc_id: Number(e.target.value), applicant_name: '', status: 'pending', is_disqualified: false, issue_note: '' }
              )}
            />
          </div>
          <div>
            <label className="form-label">서류 상태</label>
            <select
              className="form-input"
              value={editing?.status || 'pending'}
              onChange={(e) => setEditing(prev => prev ? { ...prev, status: e.target.value } : null)}
            >
              {ALLOWED_STATUSES.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="mb-4">
          <label className="form-label">결격 처리</label>
          <div className="flex items-center gap-3">
            {[false, true].map((val) => (
              <label key={String(val)} className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="radio"
                  name="disqualified"
                  checked={editing?.is_disqualified === val}
                  onChange={() => setEditing(prev => prev ? { ...prev, is_disqualified: val } : null)}
                />
                {val ? '결격 등록' : '정상'}
              </label>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <label className="form-label">비고 / 사유</label>
          <input
            type="text"
            className="form-input"
            placeholder="사유 입력"
            value={editing?.issue_note || ''}
            onChange={(e) => setEditing(prev => prev ? { ...prev, issue_note: e.target.value } : null)}
          />
        </div>

        <div className="flex gap-2">
          <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving || !editing?.doc_id}>
            {saving ? '저장 중…' : '저장'}
          </button>
          {editing && (
            <button className="btn btn-sm" onClick={() => setEditing(null)}>취소</button>
          )}
        </div>
      </div>

      {editing?.is_disqualified && (
        <div className="mt-3 px-4 py-2.5 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
          결격 등록 시 지원자 상태가 <Badge value="불합격" /> 으로 자동 변경됩니다. (합격자 제외)
        </div>
      )}
    </div>
  )
}
