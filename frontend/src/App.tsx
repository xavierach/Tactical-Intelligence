import { useEffect, useMemo, useState } from 'react'
import './App.css'

type Competition = {
  competition_id: number
  season_id: number
  competition_name: string
  season_name: string
  country_name?: string
}

type Match = {
  match_id: number
  competition_id: number
  season_id: number
  competition_name: string
  season_name: string
  home_team: string
  away_team: string
  match_date?: string
  kick_off?: string
}

  type Report = {
  match: {
    match_id: number | string
    competition: string
    season: string
    home_team: string
    away_team: string
    focus_team?: string | null
    kickoff?: string | null
    venue?: string | null
  }
  summary: {
    match: {
      match_id: number | string
      competition: string
      season: string
      home_team: string
      away_team: string
      focus_team?: string | null
      kickoff?: string | null
      venue?: string | null
    }
    attacking: {
      headline: string
      metrics: Record<string, number | string | boolean | null>
      central_players?: string[]
      top_connections?: Array<{
        source: string
        target: string
        weight: number
      }>
      summary: string
    }
    defensive: {
      headline: string
      metrics: Record<string, number | string | boolean | null>
      dominant_team?: string
      team_breakdown?: Array<Record<string, unknown>>
      gaps?: Array<Record<string, unknown>>
      summary: string
    }
    players: {
      headline: string
      metrics: Record<string, number | string | boolean | null>
      top_player?: Record<string, unknown>
      players?: Array<Record<string, unknown>>
      summary: string
    }
    tempo: {
      headline: string
      metrics: Record<string, number | string | boolean | null>
      dominant_team?: string
      team_breakdown?: Array<Record<string, unknown>>
      possessions?: Array<Record<string, unknown>>
      summary: string
    }
    themes: string[]
    evidence: string[]
    confidence: string
  }
  sections: Array<{
    title: string
    summary: string
    bullets: string[]
  }>
  analytics: Record<string, unknown>
  insights: Array<{
    section: string
    headline: string
    evidence: string[]
    implication: string
    recommendation: string
    confidence: string
  }>
  visualisations: Array<{
    id: string
    title: string
    description: string
  }>
  notes: string[]
}

type MatchesResponse = {
  matches: Match[]
}

type CompetitionsResponse = {
  competitions: Competition[]
}

type ReportResponse = {
  report: Report
}

type PassingNetworkNode = {
  name: string
  display_name?: string
  position_abbr?: string
  position_name?: string
  x?: number
  y?: number
  completed_passes: number
  passes_received: number
  outgoing_weight: number
  incoming_weight: number
  unique_connections: number
  weighted_degree: number
  betweenness: number
  event_count?: number
  has_location?: boolean
}

type PassingNetworkEdge = {
  source: string
  target: string
  weight: number
}

type PassingNetworkData = {
  summary?: string
  metrics?: Record<string, number>
  central_players?: string[]
  top_connections?: PassingNetworkEdge[]
  nodes?: PassingNetworkNode[]
  edges?: PassingNetworkEdge[]
  notes?: string[]
}

type PassingNetworkLayoutNode = PassingNetworkNode & {
  x: number
  y: number
  radius: number
  isCentral: boolean
}

type PassingNetworkLayoutEdge = PassingNetworkEdge & {
  x1: number
  y1: number
  x2: number
  y2: number
  width: number
}

type DefensiveSpacingAction = {
  team: string
  type: string
  x: number
  y: number
}

type DefensiveSpacingGap = {
  axis: 'x' | 'y'
  team: string
  gaps: Array<{
    start: number
    end: number
    gap: number
  }>
}

type DefensiveSpacingData = {
  summary?: string
  metrics?: Record<string, number | string>
  team_breakdown?: Array<{
    team: string
    defensive_actions: number
    share: number
  }>
  gaps?: DefensiveSpacingGap[]
  actions?: DefensiveSpacingAction[]
  notes?: string[]
}

type DefensiveSpacingHeatCell = {
  x: number
  y: number
  width: number
  height: number
  count: number
  opacity: number
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ?? 'http://localhost:8000'

function competitionKey(competition: Competition) {
  return `${competition.competition_id}:${competition.season_id}`
}

function formatMatchLabel(match: Match) {
  const when = match.match_date || match.kick_off || 'Date unavailable'
  return `${match.home_team} vs ${match.away_team} · ${when}`
}

function formatSpacingZone(cell: { x: number; y: number; width: number; height: number }) {
  const xStart = Math.round(cell.x)
  const xEnd = Math.round(cell.x + cell.width)
  const yStart = Math.round(cell.y)
  const yEnd = Math.round(cell.y + cell.height)
  return `Zone ${xStart}-${xEnd} / ${yStart}-${yEnd}`
}

function buildPassingNetworkLayout(network: PassingNetworkData | undefined | null) {
  if (!network?.nodes?.length || !network?.edges?.length) {
    return null
  }

  const nodes = [...network.nodes].sort(
    (left, right) => right.weighted_degree - left.weighted_degree || right.completed_passes - left.completed_passes,
  )
  const maxWeightedDegree = Math.max(...nodes.map((node) => node.weighted_degree), 1)
  const maxEdgeWeight = Math.max(...network.edges.map((edge) => edge.weight), 1)
  const hasPitchCoordinates = nodes.every((node) => typeof node.x === 'number' && typeof node.y === 'number')
  const centerX = 60
  const centerY = 40
  const ringRadius = nodes.length > 1 ? 26 : 0
  const centralPlayers = new Set(network.central_players ?? [])
  const primaryNode = nodes[0]
  const positionByName = new Map<string, { x: number; y: number }>()

  if (hasPitchCoordinates) {
    nodes.forEach((node) => {
      positionByName.set(node.name, {
        x: node.x ?? centerX,
        y: node.y ?? centerY,
      })
    })
  } else {
    nodes.forEach((node, index) => {
      if (index === 0) {
        positionByName.set(node.name, { x: centerX, y: centerY })
        return
      }

      const angle = (2 * Math.PI * (index - 1)) / Math.max(nodes.length - 1, 1) - Math.PI / 2
      positionByName.set(node.name, {
        x: centerX + ringRadius * Math.cos(angle),
        y: centerY + ringRadius * Math.sin(angle),
      })
    })
  }

  const layoutNodes: PassingNetworkLayoutNode[] = nodes.map((node) => {
    const position = positionByName.get(node.name) ?? { x: centerX, y: centerY }
    return {
      ...node,
      x: position.x,
      y: position.y,
      radius: 3 + (node.weighted_degree / maxWeightedDegree) * 4.5,
      isCentral: centralPlayers.has(node.name) || node.name === primaryNode.name,
    }
  })

  const layoutEdges: PassingNetworkLayoutEdge[] = network.edges
    .map((edge) => {
      const source = positionByName.get(edge.source)
      const target = positionByName.get(edge.target)
      if (!source || !target) {
        return null
      }

      return {
        ...edge,
        x1: source.x,
        y1: source.y,
        x2: target.x,
        y2: target.y,
        width: 0.8 + (edge.weight / maxEdgeWeight) * 2.8,
      }
    })
    .filter((edge): edge is PassingNetworkLayoutEdge => edge !== null)
    .sort((left, right) => right.width - left.width)

  return {
    nodes: layoutNodes,
    edges: layoutEdges,
    summary: network.summary || 'Passing network built from the backend analytics layer.',
    topConnections: network.top_connections?.length ? network.top_connections : network.edges.slice(0, 5),
    centralPlayers: network.central_players ?? layoutNodes.slice(0, 4).map((node) => node.name),
  }
}

function buildDefensiveSpacingLayout(data: DefensiveSpacingData | undefined | null) {
  if (!data?.actions?.length) {
    return null
  }

  const actions = [...data.actions]
  const maxActions = Math.max(actions.length, 1)
  const centroidX = Number(data.metrics?.centroid_x ?? 60)
  const centroidY = Number(data.metrics?.centroid_y ?? 40)
  const compactness = Number(data.metrics?.compactness ?? 0.5)
  const lineStretch = Number(data.metrics?.line_stretch ?? 0.5)
  const cols = 6
  const rows = 4
  const cellWidth = 120 / cols
  const cellHeight = 80 / rows
  const binCounts = new Map<string, number>()

  actions.forEach((action) => {
    const col = Math.min(cols - 1, Math.max(0, Math.floor(action.x / cellWidth)))
    const row = Math.min(rows - 1, Math.max(0, Math.floor(action.y / cellHeight)))
    const key = `${col}:${row}`
    binCounts.set(key, (binCounts.get(key) ?? 0) + 1)
  })

  const maxBinCount = Math.max(...binCounts.values(), 1)
  const heatmap: DefensiveSpacingHeatCell[] = []
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const count = binCounts.get(`${col}:${row}`) ?? 0
      if (!count) {
        continue
      }
      heatmap.push({
        x: col * cellWidth,
        y: row * cellHeight,
        width: cellWidth,
        height: cellHeight,
        count,
        opacity: 0.12 + (count / maxBinCount) * 0.68,
      })
    }
  }

  const hotZones = [...heatmap]
    .sort((left, right) => right.count - left.count)
    .slice(0, 3)

  const gapBands = (data.gaps ?? []).flatMap((gap) =>
    gap.gaps.slice(0, 2).map((item) => ({
      axis: gap.axis,
      start: item.start,
      end: item.end,
      team: gap.team,
      gap: item.gap,
    })),
  )

  return {
    centroid: {
      x: centroidX,
      y: centroidY,
    },
    gapBands,
    summary: data.summary || 'Defensive spacing from the backend analytics layer.',
    compactness,
    lineStretch,
    teamBreakdown: data.team_breakdown ?? [],
    totalActions: maxActions,
    heatmap,
    hotZones,
  }
}

function App() {
  const [competitions, setCompetitions] = useState<Competition[]>([])
  const [selectedCompetitionKey, setSelectedCompetitionKey] = useState('')
  const [matches, setMatches] = useState<Match[]>([])
  const [selectedMatchId, setSelectedMatchId] = useState('')
  const [selectedReportTeam, setSelectedReportTeam] = useState('')
  const [report, setReport] = useState<Report | null>(null)
  const [loadingCompetitions, setLoadingCompetitions] = useState(true)
  const [loadingMatches, setLoadingMatches] = useState(false)
  const [generatingReport, setGeneratingReport] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectedCompetition = useMemo(
    () => competitions.find((competition) => competitionKey(competition) === selectedCompetitionKey),
    [competitions, selectedCompetitionKey],
  )

  const selectedMatch = useMemo(
    () => matches.find((match) => String(match.match_id) === selectedMatchId),
    [matches, selectedMatchId],
  )

  useEffect(() => {
    if (!selectedMatch) {
      setSelectedReportTeam('')
      return
    }

    setSelectedReportTeam((currentTeam) => {
      if (currentTeam === selectedMatch.home_team || currentTeam === selectedMatch.away_team) {
        return currentTeam
      }
      return selectedMatch.home_team
    })
  }, [selectedMatch])

  useEffect(() => {
    let cancelled = false

    async function loadCompetitions() {
      setLoadingCompetitions(true)
      setError(null)
      try {
        const response = await fetch(`${apiBaseUrl}/api/competitions`)
        if (!response.ok) {
          throw new Error(`Failed to load competitions (${response.status})`)
        }
        const data = (await response.json()) as CompetitionsResponse
        if (cancelled) {
          return
        }

        setCompetitions(data.competitions)
        const firstCompetition = data.competitions[0]
        if (firstCompetition) {
          setSelectedCompetitionKey(competitionKey(firstCompetition))
        }
      } catch (error) {
        if (!cancelled) {
          setError(error instanceof Error ? error.message : 'Unable to load competitions')
        }
      } finally {
        if (!cancelled) {
          setLoadingCompetitions(false)
        }
      }
    }

    loadCompetitions()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const currentCompetition = selectedCompetition
    if (!currentCompetition) {
      setMatches([])
      setSelectedMatchId('')
      return
    }

    let cancelled = false

    async function loadMatches(competitionId: number, seasonId: number) {
      setLoadingMatches(true)
      setError(null)
      setReport(null)

      try {
        const params = new URLSearchParams({
          competition_id: String(competitionId),
          season_id: String(seasonId),
        })
        const response = await fetch(`${apiBaseUrl}/api/matches?${params.toString()}`)
        if (!response.ok) {
          throw new Error(`Failed to load matches (${response.status})`)
        }
        const data = (await response.json()) as MatchesResponse
        if (cancelled) {
          return
        }

        setMatches(data.matches)
        setSelectedMatchId(data.matches[0] ? String(data.matches[0].match_id) : '')
      } catch (error) {
        if (!cancelled) {
          setError(error instanceof Error ? error.message : 'Unable to load matches')
          setMatches([])
          setSelectedMatchId('')
        }
      } finally {
        if (!cancelled) {
          setLoadingMatches(false)
        }
      }
    }

    loadMatches(currentCompetition.competition_id, currentCompetition.season_id)

    return () => {
      cancelled = true
    }
  }, [selectedCompetition])

  async function generateReport() {
    if (!selectedMatch) {
      return
    }

    setGeneratingReport(true)
    setError(null)

    try {
      const response = await fetch(`${apiBaseUrl}/api/reports/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          match: selectedMatch,
          focus_team: selectedReportTeam || selectedMatch.home_team,
        }),
      })

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as
          | { error?: string }
          | null
        throw new Error(payload?.error || `Failed to generate report (${response.status})`)
      }

      const data = (await response.json()) as ReportResponse
      setReport(data.report)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to generate report')
    } finally {
      setGeneratingReport(false)
    }
  }

  const reportSections = report?.sections ?? []
  const summary = report?.summary
  const insights = report?.insights ?? []
  const narrativeNotes = report?.notes ?? []
  const reportFocusTeam = selectedReportTeam || selectedMatch?.home_team || 'Home Team'
  const passingNetwork = useMemo(
    () => buildPassingNetworkLayout(report?.analytics?.passing_network as PassingNetworkData | undefined),
    [report],
  )
  const defensiveSpacing = useMemo(
    () => buildDefensiveSpacingLayout(report?.analytics?.defensive_spacing as DefensiveSpacingData | undefined),
    [report],
  )
  const summaryCards = summary
    ? [
        {
          key: 'attacking',
          title: 'Attacking Structure',
          payload: summary.attacking,
        },
        {
          key: 'defensive',
          title: 'Defensive Shape',
          payload: summary.defensive,
        },
        {
          key: 'players',
          title: 'Player Impact',
          payload: summary.players,
        },
        {
          key: 'tempo',
          title: 'Tempo Profile',
          payload: summary.tempo,
        },
      ]
    : []

  return (
    <main className="app-shell">
      <section className="hero-panel">
        <div className="hero-copy">
          <span className="eyebrow">AI Tactical Report Generator</span>
          <h1>Turn StatsBomb open data into analyst-style football reporting.</h1>
          <p className="lede">
            Select a competition, choose a match, and generate a structured report
            with analytics, tactical interpretation, and supporting visualisation
            hooks.
          </p>

          <div className="api-banner">
            <span>API</span>
            <strong>{apiBaseUrl}</strong>
          </div>

          <div className="hero-meta">
            <div>
              <strong>Data source</strong>
              <span>statsbombpy</span>
            </div>
            <div>
              <strong>Output</strong>
              <span>API JSON for React rendering</span>
            </div>
            <div>
              <strong>Goal</strong>
              <span>Explainable tactical insight</span>
            </div>
          </div>
        </div>

        <aside className="control-panel">
          <div className="control-group">
            <label htmlFor="competition">Competition</label>
            <select
              id="competition"
              value={selectedCompetitionKey}
              onChange={(event) => setSelectedCompetitionKey(event.target.value)}
              disabled={loadingCompetitions}
            >
              {competitions.map((competition) => (
                <option key={competitionKey(competition)} value={competitionKey(competition)}>
                  {competition.competition_name} · {competition.season_name}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label htmlFor="match">Match</label>
            <select
              id="match"
              value={selectedMatchId}
              onChange={(event) => setSelectedMatchId(event.target.value)}
              disabled={loadingMatches || matches.length === 0}
            >
              {matches.map((match) => (
                <option key={match.match_id} value={match.match_id}>
                  {formatMatchLabel(match)}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label htmlFor="report-team">Report team</label>
            <select
              id="report-team"
              value={selectedReportTeam}
              onChange={(event) => setSelectedReportTeam(event.target.value)}
              disabled={!selectedMatch}
            >
              {selectedMatch ? (
                <>
                  <option value={selectedMatch.home_team}>{selectedMatch.home_team}</option>
                  <option value={selectedMatch.away_team}>{selectedMatch.away_team}</option>
                </>
              ) : null}
            </select>
          </div>

          <button
            type="button"
            className="primary-button"
            onClick={generateReport}
            disabled={!selectedMatch || generatingReport}
          >
            {generatingReport ? 'Generating report…' : 'Generate Report'}
          </button>

          <div className="status-row">
            <span>{loadingCompetitions ? 'Loading competitions…' : 'Competitions ready'}</span>
            <span>{loadingMatches ? 'Loading matches…' : 'Matches ready'}</span>
          </div>
        </aside>
      </section>

      {error ? <section className="alert">{error}</section> : null}

      <section className="content-grid">
        <article className="panel">
          <div className="panel-heading">
            <h2>Match Context</h2>
            <p>Selected fixture details and report metadata.</p>
          </div>

          {selectedMatch ? (
            <div className="context-grid">
              <div>
                <span className="label">Fixture</span>
                <strong>
                  {selectedMatch.home_team} vs {selectedMatch.away_team}
                </strong>
              </div>
              <div>
                <span className="label">Competition</span>
                <strong>{selectedMatch.competition_name}</strong>
              </div>
              <div>
                <span className="label">Season</span>
                <strong>{selectedMatch.season_name}</strong>
              </div>
              <div>
                <span className="label">Match date</span>
                <strong>{selectedMatch.match_date || selectedMatch.kick_off || 'Unknown'}</strong>
              </div>
              <div>
                <span className="label">Report focus</span>
                <strong>{reportFocusTeam}</strong>
              </div>
            </div>
          ) : (
            <p className="empty-state">Choose a match to build the report.</p>
          )}
        </article>

        <article className="panel">
          <div className="panel-heading">
            <h2>Match Summary</h2>
            <p>Backend-built summary contract passed to the LLM layer.</p>
          </div>

          {summary ? (
            <div className="summary-stack">
              <div className="summary-overview">
                  <div className="summary-overview-header">
                  <div>
                    <span className="label">LLM contract</span>
                    <h3>
                      {summary.match.home_team} vs {summary.match.away_team}
                    </h3>
                  </div>
                  <span className={`confidence-pill confidence-${summary.confidence}`}>
                    {summary.confidence} confidence
                  </span>
                </div>

                <div className="summary-match-grid">
                  <div>
                    <span className="label">Competition</span>
                    <strong>{summary.match.competition}</strong>
                  </div>
                  <div>
                    <span className="label">Season</span>
                    <strong>{summary.match.season}</strong>
                  </div>
                  <div>
                    <span className="label">Fixture</span>
                    <strong>
                      {summary.match.home_team} vs {summary.match.away_team}
                    </strong>
                  </div>
                  <div>
                    <span className="label">Kickoff</span>
                    <strong>{summary.match.kickoff || 'Unknown'}</strong>
                  </div>
                  <div>
                    <span className="label">Focus team</span>
                    <strong>{summary.match.focus_team || 'Home Team'}</strong>
                  </div>
                </div>
              </div>

              <div className="summary-card-grid">
                {summaryCards.map(({ key, title, payload }) => (
                  <article key={key} className="summary-card">
                    <div className="summary-card-header">
                      <span className="metric-label">{title}</span>
                      <strong>{payload.headline}</strong>
                    </div>
                    <p className="summary-copy">{payload.summary}</p>
                  </article>
                ))}
              </div>

              <div className="summary-panels">
                <article className="summary-panel">
                  <h3>Themes</h3>
                  {summary.themes.length > 0 ? (
                    <div className="theme-list">
                      {summary.themes.map((theme) => (
                        <span key={theme} className="theme-chip">
                          {theme}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-state">No themes were generated for this report.</p>
                  )}
                </article>

                <article className="summary-panel">
                  <h3>Overview</h3>
                  <ul className="overview-list">
                    <li>Focus team: {summary.match.focus_team || summary.match.home_team}</li>
                    <li>Competition: {summary.match.competition}</li>
                    <li>Season: {summary.match.season}</li>
                    <li>{summary.match.home_team} vs {summary.match.away_team}</li>
                  </ul>
                  <p className="summary-note">
                    Use the actionable insights section below for the detailed evidence and tactical reasoning.
                  </p>
                </article>
              </div>
            </div>
          ) : (
            <p className="empty-state">
              Run a report to see the backend summary, themes, evidence, and confidence.
            </p>
          )}
        </article>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>Actionable Insights</h2>
          <p>Claim, evidence, implication, and recommendation for the LLM.</p>
        </div>

        {insights.length > 0 ? (
          <div className="insight-grid">
            {insights.map((insight) => (
              <article key={`${insight.section}:${insight.headline}`} className="insight-card">
                <div className="insight-header">
                  <span>{insight.section}</span>
                  <strong>{insight.confidence} confidence</strong>
                </div>
                <h3>{insight.headline}</h3>
                <p>{insight.implication}</p>
                <div className="insight-block">
                  <span>Evidence</span>
                  <ul>
                    {insight.evidence.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div className="insight-block">
                  <span>Recommendation</span>
                  <p>{insight.recommendation}</p>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="empty-state">Generate a report to see LLM-ready tactical insights.</p>
        )}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>Tactical Report</h2>
          <p>Human-readable narrative generated from structured analytics.</p>
        </div>

        {reportSections.length > 0 ? (
          <div className="report-layout">
            <div className="report-sections">
              {reportSections.map((section) => (
                <article key={section.title} className="report-card">
                  <h3>{section.title}</h3>
                  <p>{section.summary}</p>
                  <ul>
                    {section.bullets.map((bullet) => (
                      <li key={bullet}>{bullet}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>

            <aside className="report-sidebar">
              <div className="subpanel">
                <h3>Passing Network</h3>
                {passingNetwork ? (
                  <div className="network-panel">
                    <p className="network-summary">{passingNetwork.summary}</p>
                    <svg
                      className="network-svg"
                      viewBox="0 0 120 80"
                      role="img"
                      aria-label="Passing network graph"
                    >
                      <defs>
                        <linearGradient id="edgeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="#f5b84a" />
                          <stop offset="100%" stopColor="#ef7d57" />
                        </linearGradient>
                      </defs>
                      <rect x="0" y="0" width="120" height="80" rx="3" className="pitch-surface" />
                      <line x1="60" y1="0" x2="60" y2="80" className="pitch-line" />
                      <circle cx="60" cy="40" r="10" className="pitch-circle" />
                      <line x1="18" y1="18" x2="18" y2="62" className="pitch-box" />
                      <line x1="102" y1="18" x2="102" y2="62" className="pitch-box" />
                      <line x1="18" y1="18" x2="0" y2="18" className="pitch-box" />
                      <line x1="18" y1="62" x2="0" y2="62" className="pitch-box" />
                      <line x1="102" y1="18" x2="120" y2="18" className="pitch-box" />
                      <line x1="102" y1="62" x2="120" y2="62" className="pitch-box" />
                      {passingNetwork.edges.map((edge, index) => (
                        <line
                          key={`${edge.source}-${edge.target}-${index}`}
                          x1={edge.x1}
                          y1={edge.y1}
                          x2={edge.x2}
                          y2={edge.y2}
                          className="network-edge"
                          style={{ strokeWidth: edge.width }}
                        />
                      ))}
                      {passingNetwork.nodes.map((node) => (
                        <g key={node.name} className={node.isCentral ? 'network-node central' : 'network-node'}>
                          <circle
                            cx={node.x}
                            cy={node.y}
                            r={node.radius}
                            className={node.isCentral ? 'network-node-core' : 'network-node-shell'}
                          />
                          <text x={node.x} y={node.y + node.radius + 3} textAnchor="middle">
                            {node.display_name || node.position_abbr || node.name}
                          </text>
                          <title>{node.name}</title>
                        </g>
                      ))}
                    </svg>

                    <div className="network-meta">
                      <div>
                        <span className="label">Central players</span>
                        <strong>
                          {passingNetwork.centralPlayers.length > 0
                            ? passingNetwork.centralPlayers.slice(0, 4).join(', ')
                            : 'No clear hub'}
                        </strong>
                      </div>
                      <div>
                        <span className="label">Top connections</span>
                        <ul className="network-connection-list">
                          {passingNetwork.topConnections.slice(0, 3).map((edge) => (
                            <li key={`${edge.source}-${edge.target}`}>
                              {edge.source} to {edge.target} ({edge.weight})
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="empty-state">Generate a report to see the passing network visualisation.</p>
                )}
              </div>

              <div className="subpanel">
                <h3>Defensive Spacing</h3>
                {defensiveSpacing ? (
                  <div className="spacing-panel">
                    <p className="network-summary">{defensiveSpacing.summary}</p>
                    <div className="spacing-callouts">
                      <span>
                        Strongest zone:{' '}
                        {defensiveSpacing.hotZones[0]
                          ? formatSpacingZone(defensiveSpacing.hotZones[0])
                          : 'N/A'}
                      </span>
                      <span>Compactness {defensiveSpacing.compactness.toFixed(2)}</span>
                      <span>Stretch {defensiveSpacing.lineStretch.toFixed(2)}</span>
                    </div>
                    <svg
                      className="spacing-svg"
                      viewBox="0 0 120 80"
                      role="img"
                      aria-label="Defensive spacing visualisation"
                    >
                      <rect x="0" y="0" width="120" height="80" rx="3" className="pitch-surface pitch-surface-alt" />
                      <line x1="60" y1="0" x2="60" y2="80" className="pitch-line" />
                      <circle cx="60" cy="40" r="10" className="pitch-circle" />
                      <line x1="18" y1="18" x2="18" y2="62" className="pitch-box" />
                      <line x1="102" y1="18" x2="102" y2="62" className="pitch-box" />
                      {defensiveSpacing.gapBands.map((band, index) =>
                        band.axis === 'x' ? (
                          <rect
                            key={`gap-x-${index}`}
                            x={band.start}
                            y={0}
                            width={Math.max(band.gap, 1)}
                            height={80}
                            className="spacing-gap-x"
                          />
                        ) : (
                          <rect
                            key={`gap-y-${index}`}
                            x={0}
                            y={band.start}
                            width={120}
                            height={Math.max(band.gap, 1)}
                            className="spacing-gap-y"
                          />
                        ),
                      )}
                      {defensiveSpacing.heatmap.map((cell, index) => (
                        <rect
                          key={`heat-${index}`}
                          x={cell.x}
                          y={cell.y}
                          width={cell.width}
                          height={cell.height}
                          className="spacing-heat-cell"
                          style={{ opacity: cell.opacity }}
                        />
                      ))}
                      <circle
                        cx={defensiveSpacing.centroid.x}
                        cy={defensiveSpacing.centroid.y}
                        r="2.4"
                        className="spacing-centroid"
                      />
                      {defensiveSpacing.hotZones.map((zone, index) => (
                        <rect
                          key={`hot-${index}`}
                          x={zone.x + 1}
                          y={zone.y + 1}
                          width={zone.width - 2}
                          height={zone.height - 2}
                          className="spacing-hot-zone"
                        />
                      ))}
                    </svg>

                    <div className="network-meta">
                      <div>
                        <span className="label">Compactness</span>
                        <strong>{defensiveSpacing.compactness.toFixed(2)}</strong>
                      </div>
                      <div>
                        <span className="label">Line stretch</span>
                        <strong>{defensiveSpacing.lineStretch.toFixed(2)}</strong>
                      </div>
                      <div>
                        <span className="label">Defensive actions</span>
                        <strong>{defensiveSpacing.totalActions}</strong>
                      </div>
                      <div>
                        <span className="label">Top zones</span>
                        <ul className="network-connection-list">
                          {defensiveSpacing.hotZones.slice(0, 3).map((zone, index) => (
                            <li key={`zone-${index}`}>
                              Zone {index + 1}: {zone.count} actions
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="empty-state">Generate a report to see the defensive spacing visualisation.</p>
                )}
              </div>

              <div className="subpanel">
                <h3>Visualisation Hooks</h3>
                <ul>
                  {(report?.visualisations ?? []).map((visualisation) => (
                    <li key={visualisation.id}>
                      <strong>{visualisation.title}</strong>
                      <span>{visualisation.description}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="subpanel">
                <h3>Narrative Notes</h3>
                <ul>
                  {narrativeNotes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </div>
            </aside>
          </div>
        ) : (
          <p className="empty-state">
            The report will appear here once you generate it from the selected match.
          </p>
        )}
      </section>
    </main>
  )
}

export default App
