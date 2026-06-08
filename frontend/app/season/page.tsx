'use client'

import { useState } from 'react'
import { closeSeason, cleanupSeason, restoreSeason } from '@/lib/api'

const SEASON_ID = 12

type ActionResult = { message: string; [key: string]: unknown }

export default function SeasonPage() {
  const [loading, setLoading] = useState<string | null>(null)
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  async function run(label: string, fn: () => Promise<ActionResult>) {
    setLoading(label)
    setMsg(null)
    try {
      const res = await fn()
      setMsg({ type: 'success', text: res.message || `${label} 완료` })
    } catch (e: unknown) {
      setMsg({ type: 'error', text: e instanceof Error ? e.message : '오류 발생' })
    } finally {
      setLoading(null)
    }
  }

  const actions = [
    {
      id: 'close',
      label: '시즌 종료',
      description: '시즌을 비활성화하고 진행중 지원자를 대기 상태로 전환합니다. Slack·이메일·Sheets 알림이 발송됩니다.',
      variant: 'default' as const,
      confirm: `Season ${SEASON_ID}을 종료하시겠습니까?\nSlack 알림, 결과 이메일, Google Sheets 동기화가 실행됩니다.`,
      fn: () => closeSeason(SEASON_ID),
    },
    {
      id: 'cleanup',
      label: '불합격자 데이터 파기',
      description: '종료된 시즌의 불합격자를 soft delete 처리합니다. 시즌이 종료된 상태여야 합니다.',
      variant: 'danger' as const,
      confirm: `Season ${SEASON_ID}의 불합격자 데이터를 파기하시겠습니까?\n이 작업은 되돌리기 어렵습니다.`,
      fn: () => cleanupSeason(SEASON_ID),
    },
    {
      id: 'restore',
      label: '시즌 복원 (시연용)',
      description: '종료된 시즌과 soft delete된 지원자 데이터를 복원합니다. 시연·테스트 용도로만 사용하세요.',
      variant: 'default' as const,
      confirm: `Season ${SEASON_ID}을 복원하시겠습니까?`,
      fn: () => restoreSeason(SEASON_ID),
    },
  ]

  return (
    <div>
      <h1 className="page-title">시즌 관리</h1>

      {msg && (
        <div className={`mb-5 px-4 py-3 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {msg.text}
          <button className="ml-3 opacity-60" onClick={() => setMsg(null)}>✕</button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 max-w-xl">
        {actions.map((action) => (
          <div key={action.id} className="card">
            <div className="flex justify-between items-start">
              <div className="flex-1 mr-4">
                <p className="text-sm font-medium mb-1">{action.label}</p>
                <p className="text-xs text-gray-500">{action.description}</p>
              </div>
              <button
                className={`btn btn-sm shrink-0 ${action.variant === 'danger' ? 'btn-danger' : ''}`}
                disabled={loading !== null}
                onClick={() => {
                  if (!confirm(action.confirm)) return
                  run(action.label, action.fn as () => Promise<ActionResult>)
                }}
              >
                {loading === action.label ? '처리 중…' : action.label}
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700 max-w-xl">
        ⚠️ 시즌 종료와 데이터 파기는 되돌리기 어렵습니다. 신중하게 실행하세요.
      </div>
    </div>
  )
}
