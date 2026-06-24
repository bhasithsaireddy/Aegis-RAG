export function normalizeMatchScore(score) {
    const value = Number(score)

    if (!Number.isFinite(value) || value <= 0) {
        return 0
    }

    let percent = value

    if (value <= 1) {
        percent = value * 100
    } else if (value <= 10) {
        percent = value * 10
    }

    return Math.max(1, Math.min(100, Math.round(percent)))
}

export function formatMatchScore(score) {
    const percent = normalizeMatchScore(score)
    return percent > 0 ? `${percent}% match` : ''
}