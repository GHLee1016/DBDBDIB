'use client'

import { useState } from 'react'
import { createEvaluation } from '@/lib/api'

const EVAL_TYPES = ['서류', '1차면접', '최종면접']

type Form = {
  applicant_id: string
  evaluator_id: string
  score: string
  eval_type: string
  comment: string
  interview_datetime: string
}

const DEFAULT_FORM: Form = {
  applicant_id: '',
  evaluator_id: '',
  score: '',
  eval_type: '서류',
  comment: '',
  interview_datetime: '',
}

export default function EvaluationsPage() {
  const [form, setForm] = useState<Form>(DEFAULT_FORM)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  function set(key: keyof Form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm(prev => ({ ...prev, [key]: e.target.value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const score = Number(form.score)
    if (score < 0 || score > 100) {
      setMsg({ type: 'error', text: '점수는 0~100 사이여야 합니다.' })
      return
    }
    setSaving(true)
    try {
      const res = await createEvaluation({
        applicant_id: Number(form.applicant_id),
        evaluator_id: Number(form.evaluator_id),
        score,
        eval_type: form.eval_type,
        comment: form.comment || undefined,
        interview_datetime: form.interview_datetime || undefined,
      }) as { avg_score: number; applicant_status?: string }

      let text = `평가 저장 완료. 현재 평균: ${res.avg_score.toFixed(1)}점`
      if (res.applicant_status) text += ` | 상태 변경: ${res.applicant_status}`
      setMsg({ type: 'success', text })
      setForm(DEFAULT_FORM)
    } catch (err: unknown) {
      setMsg({ type: 'error', text: err instanceof Error ? err.message : '오류 발생' })
    } finally {
      setSaving(false)
    }
  }

  const needsDatetime = form.eval_type === '1차면접' || form.eval_type === '최종면접'

  return (
    <div>
      <h1 className="page-title">평가 점수 입력</h1>

      {msg && (
        <div className={`mb-4 px-4 py-2.5 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {msg.text}
          <button className="ml-3 opacity-60 hover:opacity-100" onClick={() => setMsg(null)}>✕</button>
        </div>
      )}

      <div className="grid grid-cols-2 gap-5">
        <form onSubmit={handleSubmit} className="card">
          <p className="text-sm font-medium mb-4">새 평가 입력</p>

          <div className="mb-3.5">
            <label className="form-label">지원자 ID</label>
            <input type="number" className="form-input" placeholder="지원자 ID" value={form.applicant_id} onChange={set('applicant_id')} required />
          </div>

          <div className="mb-3.5">
            <label className="form-label">평가자 ID</label>
            <input type="number" className="form-input" placeholder="평가자 ID" value={form.evaluator_id} onChange={set('evaluator_id')} required />
          </div>

          <div className="mb-3.5">
            <label className="form-label">전형 단계</label>
            <select className="form-input" value={form.eval_type} onChange={set('eval_type')}>
              {EVAL_TYPES.map(t => <option key={t}>{t}</option>)}
            </select>
          </div>

          <div className="mb-3.5">
            <label className="form-label">점수 (0–100)</label>
            <input type="number" className="form-input" placeholder="점수 입력" min={0} max={100} value={form.score} onChange={set('score')} required />
          </div>

          {needsDatetime && (
            <div className="mb-3.5">
              <label className="form-label">면접 일시 <span className="text-gray-400">(선택)</span></label>
              <input type="text" className="form-input" placeholder="2026-06-10T14:00:00" value={form.interview_datetime} onChange={set('interview_datetime')} />
              <p className="text-xs text-gray-400 mt-1">입력 시 Google Calendar에 자동 등록됩니다.</p>
            </div>
          )}

          <div className="mb-4">
            <label className="form-label">코멘트</label>
            <textarea className="form-input" rows={3} placeholder="평가 코멘트를 입력하세요" value={form.comment} onChange={set('comment')} />
          </div>

          <button type="submit" className="btn btn-primary w-full" disabled={saving}>
            {saving ? '저장 중…' : '평가 저장'}
          </button>
        </form>

        <div className="card">
          <p className="text-sm font-medium mb-4">안내</p>
          <div className="space-y-3 text-sm text-gray-500">
            <p>• 점수 입력 후 평균이 <strong className="text-gray-700">80점 이상</strong>이면 지원자 상태가 <strong className="text-gray-700">진행중 → 대기</strong>로 자동 변경됩니다.</p>
            <p>• 1차면접, 최종면접의 경우 면접 일시를 입력하면 Google Calendar에 이벤트가 생성됩니다.</p>
            <p>• 평가 유형: 서류 / 1차면접 / 최종면접</p>
          </div>
        </div>
      </div>
    </div>
  )
}
