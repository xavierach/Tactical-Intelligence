import type { Match } from '../types'

type Props = {
  selectedMatch: Match | undefined
  reportFocusTeam: string
}

export function MatchContextPanel({ selectedMatch, reportFocusTeam }: Props) {
  return (
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
  )
}

