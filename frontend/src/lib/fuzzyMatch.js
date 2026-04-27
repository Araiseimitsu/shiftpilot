/** 簡易あいまいマッチングユーティリティ */

/**
 * レーベンシュタイン距離を計算する
 */
function levenshtein(a, b) {
  const m = a.length, n = b.length
  if (m === 0) return n
  if (n === 0) return m

  const matrix = Array.from({ length: m + 1 }, (_, i) => {
    const row = new Array(n + 1)
    row[0] = i
    return row
  })
  for (let j = 1; j <= n; j++) matrix[0][j] = j

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + cost
      )
    }
  }
  return matrix[m][n]
}

/**
 * 最も近いメンバー名を探す。
 * 優先順位: 完全一致 > 部分一致 > 編集距離（閾値0.5未満）
 */
export function findBestMatch(input, candidates) {
  if (!input || candidates.length === 0) return { name: null, score: 0, method: null }

  // 完全一致
  const exact = candidates.find(c => c === input)
  if (exact) return { name: exact, score: 1, method: 'exact' }

  // 部分一致（双方向）
  const partial = candidates.find(c => c.includes(input) || input.includes(c))
  if (partial) return { name: partial, score: 0.9, method: 'partial' }

  // 編集距離による類似度（長い方を分母）
  let best = null
  let bestScore = -1
  const maxLen = Math.max(...candidates.map(c => c.length), input.length)

  for (const c of candidates) {
    const dist = levenshtein(input, c)
    const sim = 1 - dist / Math.max(input.length, c.length)
    if (sim > bestScore) {
      bestScore = sim
      best = c
    }
  }

  // 類似度が0.5以上なら採用
  if (best && bestScore >= 0.5) {
    return { name: best, score: bestScore, method: 'fuzzy' }
  }

  return { name: null, score: 0, method: null }
}
