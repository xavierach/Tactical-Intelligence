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
    kickoff?: string | null
    venue?: string | null
  }
  sections: Array<{
    title: string
    summary: string
    bullets: string[]
  }>
  analytics: Record<string, unknown>
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

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ?? 'http://localhost:8000'

function competitionKey(competition: Competition) {
  return `${competition.competition_id}:${competition.season_id}`
}

function formatMatchLabel(match: Match) {
  const when = match.match_date || match.kick_off || 'Date unavailable'
  return `${match.home_team} vs ${match.away_team} · ${when}`
}

function App() {
  const [competitions, setCompetitions] = useState<Competition[]>([])
  const [selectedCompetitionKey, setSelectedCompetitionKey] = useState('')
  const [matches, setMatches] = useState<Match[]>([])
  const [selectedMatchId, setSelectedMatchId] = useState('')
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
  const analyticsEntries = Object.entries(report?.analytics ?? {})
  const narrativeNotes = report?.notes ?? []

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
            </div>
          ) : (
            <p className="empty-state">Choose a match to build the report.</p>
          )}
        </article>

        <article className="panel">
          <div className="panel-heading">
            <h2>Analytics Snapshot</h2>
            <p>Structured metrics passed to the LLM layer.</p>
          </div>

          <div className="metrics-grid">
            {analyticsEntries.length > 0 ? (
              analyticsEntries.map(([key, value]) => (
                <div key={key} className="metric-card">
                  <span className="metric-label">{key.replaceAll('_', ' ')}</span>
                  <pre>{JSON.stringify(value, null, 2)}</pre>
                </div>
              ))
            ) : (
              <p className="empty-state">Run a report to see passing, defensive, player, and tempo outputs.</p>
            )}
          </div>
        </article>
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
