'use client'

import { useEffect, useState } from 'react'
import { listDocuments, updateDocument, Document } from '@/lib/api'

const SEASON_ID = 1
const ALLOWED_STATUSES = ['pending', 'verified', 'missing', 'incomplete']

const STATUS_LABELS: Record<string, string> = {
  pending:    '검토 대기',
  verified:   '확인 완료',
  missing:    '미제출',
  incomplete: '불완전',
}

export default function DocumentsPage() {
  const [docs, setDocs]         = useState<Document[]>([])
  const [loading, setLoading]   = useState(true)
  const [editing, setEditing]   = useState<Document | null>(null)
  const [form, setForm]         = useState({ status: 'pending', is_disqualified: false, issue_note: '' })
  const [saving, setSaving]     = useState(false)
  const [search, setSearch]     = useState('')
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  function load() {
    setLoading(true)
    listDocuments(SEASON_ID)
      .then(setDocs)
      .catch(() => setDocs([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  function openEdit(doc: Document) {
    setEditing(doc)
    setForm({
      status: doc.status,
      is_disqualified: doc.is_disqualified,
      issue_note: doc.issue_note ?? '',
    })
  }

  async function handleSave() {
    if (!editing) return
    setSaving(true)
    try {
      await updateDocument(editing.doc_id, form)
      setMsg({ type: 'success', text: `${editing.name} 서류 업데이트 완료` })
      setEditing(null)
      load()
    } catch (e: unknown) {
      setMsg({ type: 'error', text: e instanceof Error ? e.message : '저장 실패' })
    } finally {
      setSaving(false)
    }
  }

  const filtered = docs.filter(d =>
    d.name.includes(search) || d.major.includes(search) || d.doc_type.includes(search)
  )

  return (
    <div>
      <div className="flex justify-between items-center mb-5">
        <h1 className="page-title">서류 관리</h1>
        <span className="text-sm text-gray-400">Season {SEASON_ID} · {docs.length}건</span>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2.5 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {msg.text}
          <button className="ml-3 opacity-60" onClick={() => setMsg(null)}>✕</button>
        </div>
      )}

      <input
        className="form-input w-full mb-4"
        placeholder="이름, 전공, 서류 유형 검색"
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      <div className="card p-0 overflow-hidden">
        {loading ? (
          <p className="text-sm text-gray-400 py-12 text-center">불러오는 중…</p>
        ) : filtered.length === 0 ? (
          <p className="text-sm text-gray-400 py-12 text-center">서류가 없습니다.</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr>
                <th>이름</th>
                <th>전공</th>
                <th>서류 유형</th>
                <th>상태</th>
                <th>결격</th>
                <th>비고</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(d => (
                <tr key={d.doc_id}>
                  <td className="font-medium">{d.name}</td>
                  <td className="text-gray-500 text-sm">{d.major}</td>
                  <td className="text-gray-500 text-sm">{d.doc_type}</td>
                  <td>
                    <span className={`badge ${d.status === 'verified' ? 'badge-pass' : d.status === 'missing' ? 'badge-fail' : 'badge-warning'}`}>
                      {STATUS_LABELS[d.status] ?? d.status}
                    </span>
                  </td>
                  <td>
                    {d.is_disqualified
                      ? <span className="badge badge-fail">결격</span>
                      : <span className="text-gray-300 text-xs">정상</span>}
                  </td>
                  <td className="text-xs text-gray-400 max-w-[150px] truncate" title={d.issue_note ?? ''}>
                    {d.issue_note || '—'}
                  </td>
                  <td>
                    <button className="btn btn-sm" onClick={() => openEdit(d)}>수정</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* 수정 모달 */}
      {editing && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h2 className="text-sm font-medium mb-4">서류 수정 — {editing.name} ({editing.doc_type})</h2>

            <div className="space-y-4">
              <div>
                <label className="form-label">서류 상태</label>
                <select
                  className="form-input w-full"
                  value={form.status}
                  onChange={e => setForm(f => ({ ...f, status: e.target.value }))}
                >
                  {ALLOWED_STATUSES.map(s => (
                    <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-label">결격 처리</label>
                <div className="flex gap-4 mt-1">
                  {[false, true].map(val => (
                    <label key={String(val)} className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="radio"
                        checked={form.is_disqualified === val}
                        onChange={() => setForm(f => ({ ...f, is_disqualified: val }))}
                      />
                      {val ? '결격 등록' : '정상'}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="form-label">비고 / 사유</label>
                <input
                  className="form-input w-full"
                  placeholder="사유 입력"
                  value={form.issue_note}
                  onChange={e => setForm(f => ({ ...f, issue_note: e.target.value }))}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button className="btn" onClick={() => setEditing(null)}>취소</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? '저장 중…' : '저장'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
