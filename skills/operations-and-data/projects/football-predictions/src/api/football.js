import axios from 'axios'

const ESPN_BASE = 'https://site.api.espn.com/apis/site/v2/sports/soccer'
const GAMMA_BASE = 'https://gamma-api.polymarket.com'

// ESPN league codes
export const LEAGUES = {
  laliga: 'esp.1',
  segunda: 'esp.2',
}

// ── ESPN: fetch matches for a date range ─────────────────────────────────────
export async function fetchMatches(league = 'laliga', daysAhead = 14) {
  try {
    const leagueCode = LEAGUES[league]
    const today = new Date()
    const end = new Date()
    end.setDate(today.getDate() + daysAhead)

    const fmt = (d) =>
      `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`

    const res = await axios.get(
      `${ESPN_BASE}/${leagueCode}/scoreboard?dates=${fmt(today)}-${fmt(end)}`
    )

    const events = res.data?.events ?? []
    return events.map((e) => {
      const comp = e.competitions?.[0] ?? {}
      const competitors = comp.competitors ?? []
      const home = competitors.find((t) => t.homeAway === 'home') ?? {}
      const away = competitors.find((t) => t.homeAway === 'away') ?? {}
      const status = e.status?.type?.name ?? ''
      const isLive = status === 'STATUS_IN_PROGRESS'
      const isFinished = status === 'STATUS_FULL_TIME' || status === 'STATUS_FINAL'

      return {
        id: e.id,
        date: e.date,
        league,
        status,
        isLive,
        isFinished,
        round: comp.notes?.[0]?.headline ?? '',
        home: {
          id: home.team?.id,
          name: home.team?.displayName ?? '',
          shortName: home.team?.shortDisplayName ?? '',
          logo: home.team?.logo ?? '',
          score: home.score ?? null,
        },
        away: {
          id: away.team?.id,
          name: away.team?.displayName ?? '',
          shortName: away.team?.shortDisplayName ?? '',
          logo: away.team?.logo ?? '',
          score: away.score ?? null,
        },
        venue: comp.venue?.fullName ?? '',
        broadcast: comp.broadcasts?.[0]?.names?.join(', ') ?? '',
      }
    })
  } catch (err) {
    console.error('fetchMatches error:', err.message)
    return []
  }
}

// ── ESPN: fetch recent past matches ──────────────────────────────────────────
export async function fetchRecentMatches(league = 'laliga', daysPast = 7) {
  try {
    const leagueCode = LEAGUES[league]
    const today = new Date()
    const start = new Date()
    start.setDate(today.getDate() - daysPast)

    const fmt = (d) =>
      `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`

    const res = await axios.get(
      `${ESPN_BASE}/${leagueCode}/scoreboard?dates=${fmt(start)}-${fmt(today)}`
    )

    const events = res.data?.events ?? []
    return events.map((e) => {
      const comp = e.competitions?.[0] ?? {}
      const competitors = comp.competitors ?? []
      const home = competitors.find((t) => t.homeAway === 'home') ?? {}
      const away = competitors.find((t) => t.homeAway === 'away') ?? {}

      return {
        id: e.id,
        date: e.date,
        league,
        isFinished: true,
        home: {
          name: home.team?.displayName ?? '',
          logo: home.team?.logo ?? '',
          score: home.score ?? '-',
        },
        away: {
          name: away.team?.displayName ?? '',
          logo: away.team?.logo ?? '',
          score: away.score ?? '-',
        },
      }
    })
  } catch (err) {
    console.error('fetchRecentMatches error:', err.message)
    return []
  }
}

// ── Prediction Markets: real season markets ───────────────────────────────────
const SEASON_EVENT_IDS = {
  championsLeague: '33506',
  laLigaWinner: '33509',
  relegated: '37971',
  topGoalscorer: '38077',
  europaLeague: '38532',
  top4: '40045',
}

export async function fetchSeasonMarkets() {
  try {
    const ids = Object.values(SEASON_EVENT_IDS).join(',')
    const res = await axios.get(`${GAMMA_BASE}/events`, {
      params: { id: ids, active: true, closed: false },
    })
    const events = Array.isArray(res.data) ? res.data : res.data?.events ?? []

    return events.map((event) => ({
      id: event.id,
      title: event.title?.trim(),
      image: event.image,
      volume: event.volume ?? 0,
      volume24hr: event.volume24hr ?? 0,
      liquidity: event.liquidity ?? 0,
      endDate: event.endDate,
      markets: (event.markets ?? [])
        .map((m) => {
          const prices = JSON.parse(m.outcomePrices || '["0","0"]')
          return {
            id: m.id,
            question: m.question,
            groupItemTitle: m.groupItemTitle || m.question,
            image: m.image,
            probability: Math.round(parseFloat(prices[0]) * 100),
            volume: m.volumeNum ?? 0,
            active: m.active,
            closed: m.closed,
          }
        })
        .filter((m) => m.active && !m.closed)
        .sort((a, b) => b.probability - a.probability),
    }))
  } catch (err) {
    console.error('fetchSeasonMarkets error:', err.message)
    return []
  }
}

export const MOCK_TIPSTERS = [
  { id: 't1', name: 'CarlosBets', avatar: 'CB', hitRate: 71, totalPicks: 348, roi: 18.4, specialty: 'La Liga' },
  { id: 't2', name: 'LaLigaGuru', avatar: 'LG', hitRate: 68, totalPicks: 512, roi: 12.1, specialty: 'La Liga' },
  { id: 't3', name: 'SegundaExpert', avatar: 'SE', hitRate: 64, totalPicks: 290, roi: 9.7, specialty: 'Segunda' },
  { id: 't4', name: 'ValueHunterES', avatar: 'VH', hitRate: 59, totalPicks: 740, roi: 22.8, specialty: 'Ambas Ligas' },
  { id: 't5', name: 'PronosticosBCN', avatar: 'PB', hitRate: 66, totalPicks: 415, roi: 14.3, specialty: 'La Liga' },
  { id: 't6', name: 'IberiaBets', avatar: 'IB', hitRate: 62, totalPicks: 198, roi: 7.2, specialty: 'Segunda' },
]
