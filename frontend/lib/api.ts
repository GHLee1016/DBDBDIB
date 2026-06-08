const BASE = process.env.NEXT_PUBLIC_API_BASE || '/api-flask'

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || 'Request failed')
  }
  return res.json()
}

// ── 공통 ──────────────────────────────────────────────
export const dbCheck = () => req('/common/db-check')

// ── 지원자 ────────────────────────────────────────────
export const listApplicants = (season_id?: number) =>
  req<Applicant[]>(`/admin/applicants${season_id ? `?season_id=${season_id}` : ''}`)

export const getApplicantStats = (id: number) =>
  req<{ name: string; avg_score: number; total_evals: number }>(
    `/admin/applicants/${id}/stats`
  )

export const reassignPaper = (id: number, paper_id?: number) =>
  req(`/admin/applicants/${id}/reassign-paper`, {
    method: 'PATCH',
    body: JSON.stringify(paper_id ? { paper_id } : {}),
  })

// ── 서류 ──────────────────────────────────────────────
export const listDocuments = (season_id?: number) =>
  req<Document[]>(`/admin/documents${season_id ? `?season_id=${season_id}` : ''}`)

export const updateDocument = (
  doc_id: number,
  data: { status: string; is_disqualified: boolean; issue_note?: string }
) => req(`/admin/documents/${doc_id}`, { method: 'PATCH', body: JSON.stringify(data) })

// ── 평가 ──────────────────────────────────────────────
export const createEvaluation = (data: {
  applicant_id: number
  evaluator_id: number
  score: number
  eval_type?: string
  comment?: string
  interview_datetime?: string
}) => req('/admin/evaluations', { method: 'POST', body: JSON.stringify(data) })

// ── 논문 배정 ──────────────────────────────────────────
export const assignPapers = (season_id: number) =>
  req(`/admin/recruiting/season/${season_id}/assign-papers`, { method: 'POST' })

export const getPaperAssignments = (season_id: number) =>
  req<PaperAssignment[]>(`/admin/recruiting/season/${season_id}/paper-assignments`)

// ── 채용 관리 ──────────────────────────────────────────
export const getDisqualifiedList = (season_id?: number) =>
  req<DisqualifiedApplicant[]>(
    `/admin/recruiting/disqualified-list${season_id ? `?season_id=${season_id}` : ''}`
  )

export const closeSeason = (season_id: number) =>
  req(`/admin/recruiting/season/${season_id}/close`, { method: 'PATCH' })

export const cleanupSeason = (season_id: number) =>
  req(`/admin/recruiting/season/${season_id}/cleanup`, { method: 'DELETE' })

export const restoreSeason = (season_id: number) =>
  req(`/admin/recruiting/season/${season_id}/restore`, { method: 'PATCH' })

// ── 통계 ──────────────────────────────────────────────
export const getSeasonPassRate = () =>
  req<SeasonPassRateResponse>('/admin/stats/season-pass-rate')

export const getPapersWithCitations = (season_id: number) =>
  req<PaperCitationResponse>(`/admin/stats/papers/${season_id}`)

// ── 타입 ──────────────────────────────────────────────
export interface Applicant {
  applicant_id: number
  name: string
  major: string
  email: string
  final_status: string
  season_id: number
  avg_score: number | null
  total_evals: number
  paper_title: string | null
  paper_difficulty: string | null
}

export interface Document {
  doc_id: number
  doc_type: string
  status: string
  is_disqualified: boolean
  issue_note: string | null
  applicant_id: number
  name: string
  major: string
  final_status: string
  season_id: number
}

export interface PaperAssignment {
  applicant_id: number
  name: string
  major: string
  paper_title: string
  paper_authors: string
  category: string
  difficulty: string
  assigned_at: string
}

export interface DisqualifiedApplicant {
  name: string
  major: string
  doc_type: string
  reason: string
}

export interface SeasonStat {
  rank: number
  season_id: number
  season_name: string
  total: number
  passed: number
  failed: number
  pending: number
  pass_rate: number
  avg_score: number | null
  major_distribution: Record<string, number>
  source: string
}

export interface SeasonPassRateResponse {
  generated_at: string
  total_seasons: number
  season_ranking: SeasonStat[]
}

export interface PaperStat {
  rank: number
  paper_id: number
  title: string
  authors: string
  category: string
  original_difficulty: string
  citation_count: number | null
  adjusted_difficulty: string
  difficulty_changed: boolean
  assigned_to: string | null
}

export interface PaperCitationResponse {
  season_id: number
  season_name: string
  generated_at: string
  total_papers: number
  difficulty_adjusted: number
  paper_ranking: PaperStat[]
}
