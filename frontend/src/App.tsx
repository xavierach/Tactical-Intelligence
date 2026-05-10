import { useEffect, useMemo, useState } from 'react'
import './App.css'
import { MatchContextPanel } from './components/MatchContextPanel'
import { MatchSummaryPanel } from './components/MatchSummaryPanel'
import { TacticalReportPanel } from './components/TacticalReportPanel'
import type { Competition, Match, Report } from './types'

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
        const payload = (await response.json().catch(() => null)) as { error?: string } | null
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
            with analytics, tactical interpretation, and supporting visualisation hooks.
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
        <MatchContextPanel selectedMatch={selectedMatch} reportFocusTeam={reportFocusTeam} />
        <MatchSummaryPanel summary={summary} summaryCards={summaryCards} />
      </section>

      <TacticalReportPanel
        report={report}
        reportSections={reportSections}
        insights={insights}
        narrativeNotes={narrativeNotes}
      />
    </main>
  )
}

export default App

