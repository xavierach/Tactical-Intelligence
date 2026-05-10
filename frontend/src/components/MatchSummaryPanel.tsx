import type { Report } from '../types'

type Props = {
  summary: Report['summary'] | undefined
  summaryCards: Array<{
    key: string
    title: string
    payload: {
      headline: string
      summary: string
    }
  }>
}

export function MatchSummaryPanel({ summary, summaryCards }: Props) {
  return (
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
                <li>
                  {summary.match.home_team} vs {summary.match.away_team}
                </li>
              </ul>
              <p className="summary-note">
                Use the tactical report section below for the detailed evidence and reasoning.
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
  )
}

