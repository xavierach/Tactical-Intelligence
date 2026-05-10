import type { DefensiveSpacingData, PassingNetworkData, Report } from '../types'
import {
  buildDefensiveSpacingLayout,
  buildPassingNetworkLayout,
  formatPlayerLastName,
  formatSpacingZone,
} from '../utils/visualisations'

type Props = {
  report: Report | null
  reportSections: Report['sections']
  insights: Report['insights']
  narrativeNotes: string[]
}

export function TacticalReportPanel({ report, reportSections, insights, narrativeNotes }: Props) {
  const passingNetwork = buildPassingNetworkLayout(report?.analytics?.passing_network as PassingNetworkData | undefined)
  const defensiveSpacing = buildDefensiveSpacingLayout(
    report?.analytics?.defensive_spacing as DefensiveSpacingData | undefined,
  )
  const insightSectionMap = {
    'Match Overview': 'match',
    'Attacking Analysis': 'attacking',
    'Defensive Analysis': 'defensive',
    'Key Players': 'players',
    'Tempo and Transitions': 'tempo',
  } as const

  const getInsightsForSection = (title: keyof typeof insightSectionMap) =>
    insights.filter((insight) => insight.section === insightSectionMap[title])

  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Tactical Report</h2>
        <p>Human-readable narrative generated from structured analytics.</p>
      </div>

      {reportSections.length > 0 ? (
        <div className="report-layout">
          <div className="report-sections">
            {reportSections.map((section) => {
              const sectionInsights = getInsightsForSection(section.title as keyof typeof insightSectionMap)
              return (
                <article key={section.title} className="report-card">
                  <h3>{section.title}</h3>
                  <p>{section.summary}</p>
                  <ul>
                    {section.bullets.map((bullet) => (
                      <li key={bullet}>{bullet}</li>
                    ))}
                  </ul>

                  {sectionInsights.length > 0 && section.title !== 'Match Overview' ? (
                    <div className="report-card-insight-group">
                      <span className="report-card-insight-heading">Recommendations</span>
                      <ul className="insight-list">
                        {sectionInsights.map((insight) => (
                          <li key={`${insight.section}:${insight.headline}`}>
                            <strong>{insight.headline}</strong>
                            <span>{insight.implication}</span>
                            <div className="insight-callout">
                              <span className="insight-label">Recommendation</span>
                              <p>{insight.recommendation}</p>
                            </div>
                            <div className="insight-callout">
                              <span className="insight-label">Why it helps</span>
                              <p>{insight.why_it_helps}</p>
                            </div>
                            <div className="insight-callout">
                              <span className="insight-label">How to apply</span>
                              <p>{insight.how_to_apply}</p>
                            </div>
                            <div className="insight-callout">
                              <span className="insight-label">Expected result</span>
                              <p>{insight.expected_result}</p>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </article>
              )
            })}
          </div>

          <aside className="report-sidebar">
            <div className="subpanel">
              <h3>Passing Network</h3>
              {passingNetwork ? (
                <div className="network-panel">
                  <p className="network-summary">{passingNetwork.summary}</p>
                  <svg className="network-svg" viewBox="0 0 120 80" role="img" aria-label="Passing network graph">
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
                          {formatPlayerLastName(node.name) || node.display_name || node.position_abbr || node.name}
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
                  {defensiveSpacing.flankBreakdown ? (
                    <div className="flank-breakdown">
                      <div className="flank-breakdown-header">
                        <span className="label">Flank pressure balance</span>
                        <span className="flank-breakdown-note">
                          Left / center / right action share
                        </span>
                      </div>
                      <div className="flank-bars" role="img" aria-label="Flank pressure balance">
                        {defensiveSpacing.flankBreakdown
                          .slice()
                          .sort((a, b) => (a.share ?? 0) - (b.share ?? 0))
                          .map((flank) => (
                            <div className="flank-bar-row" key={String(flank.flank ?? flank.third ?? flank.zone)}>
                              <div className="flank-bar-label">
                                <strong>{String(flank.flank ?? flank.third ?? flank.zone ?? 'Zone')}</strong>
                                <span>{Number(flank.defensive_actions ?? 0)} actions</span>
                              </div>
                              <div className="flank-bar-track">
                                <div
                                  className={`flank-bar-fill flank-${String(flank.flank ?? flank.third ?? flank.zone ?? 'zone')}`}
                                  style={{ width: `${Math.max(8, Math.round((Number(flank.share ?? 0) || 0) * 100))}%` }}
                                />
                              </div>
                              <span className="flank-bar-share">
                                {Math.round((Number(flank.share ?? 0) || 0) * 100)}%
                              </span>
                            </div>
                          ))}
                      </div>
                    </div>
                  ) : null}
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
                          <li key={`zone-${index}`}>Zone {index + 1}: {zone.count} actions</li>
                        ))}
                      </ul>
                    </div>
                    {defensiveSpacing.flankBreakdown ? (
                      <div>
                        <span className="label">Flank pressure</span>
                        <ul className="network-connection-list">
                        {defensiveSpacing.flankBreakdown.slice(0, 3).map((flank, index) => (
                          <li key={`flank-${index}`}>
                            {String(flank.flank ?? flank.third ?? flank.zone)}: {Number(flank.defensive_actions ?? 0)} actions
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
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
  )
}
