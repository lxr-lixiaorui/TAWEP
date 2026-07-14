export type QuestionMessage = {
  speaker_role: 'professor' | 'student_a' | 'student_b'
  speaker_name: string
  content: string
  sort_order: number
}

export type AdminQuestion = {
  id: string
  question_no: number
  source: 'official' | 'user'
  status: 'pending' | 'accepted' | 'rejected'
  topic: string
  topic_key: string
  exam_type: 'classic' | 'reform_2026'
  difficulty: 'easy' | 'medium' | 'hard'
  summary: string
  avg_score: number | null
  word_count: number
  creator_id: string | null
  creator_alias: string | null
  creator_email: string | null
  session_count: number
  messages: QuestionMessage[]
  created_at: string
}

export type QuestionReview = {
  review_id: string
  question: AdminQuestion
  reviewer_id: string | null
  reviewer_alias: string | null
  status: 'pending' | 'accepted' | 'rejected'
  comment: string | null
  reviewed_at: string | null
}

export function questionMessage(question: AdminQuestion, role: QuestionMessage['speaker_role']) {
  return question.messages.find((item) => item.speaker_role === role)
}
