const STATUS_CLASS: Record<string, string> = {
  합격: 'badge-pass',
  불합격: 'badge-fail',
  진행중: 'badge-info',
  대기: 'badge-warning',
  verified: 'badge-pass',
  pending: 'badge-warning',
  missing: 'badge-fail',
  incomplete: 'badge-warning',
  hard: 'badge-fail',
  medium: 'badge-warning',
  easy: 'badge-pass',
}

export default function Badge({ value }: { value: string }) {
  const cls = STATUS_CLASS[value] || 'badge-warning'
  return <span className={`badge ${cls}`}>{value}</span>
}
