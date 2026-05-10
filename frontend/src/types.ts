export type Competition = {
  competition_id: number
  season_id: number
  competition_name: string
  season_name: string
  country_name?: string
}

export type Match = {
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

export type Report = {
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
      routes?: Array<Record<string, unknown>>
      best_route?: Record<string, unknown>
      route_summary?: string
      sequence_breakdown?: Array<Record<string, unknown>>
      best_sequence?: Record<string, unknown>
      sequence_examples?: Array<Record<string, unknown>>
      sequence_summary?: string
      summary: string
    }
    defensive: {
      headline: string
      metrics: Record<string, number | string | boolean | null>
      dominant_team?: string
      team_breakdown?: Array<Record<string, unknown>>
      flank_breakdown?: Array<Record<string, unknown>>
      zone_breakdown?: Array<Record<string, unknown>>
      flank_pressure_gaps?: Array<Record<string, unknown>>
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
    why_it_helps: string
    how_to_apply: string
    expected_result: string
    confidence: string
  }>
  visualisations: Array<{
    id: string
    title: string
    description: string
  }>
  notes: string[]
}

export type PassingNetworkNode = {
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

export type PassingNetworkEdge = {
  source: string
  target: string
  weight: number
}

export type PassingNetworkData = {
  summary?: string
  metrics?: Record<string, number>
  central_players?: string[]
  top_connections?: PassingNetworkEdge[]
  nodes?: PassingNetworkNode[]
  edges?: PassingNetworkEdge[]
  notes?: string[]
}

export type DefensiveSpacingAction = {
  team: string
  type: string
  x: number
  y: number
}

export type DefensiveSpacingGap = {
  axis: 'x' | 'y'
  team: string
  gaps: Array<{
    start: number
    end: number
    gap: number
  }>
}

export type DefensiveSpacingData = {
  summary?: string
  metrics?: Record<string, number | string>
  team_breakdown?: Array<{
    team: string
    defensive_actions: number
    share: number
  }>
  flank_breakdown?: Array<{
    flank?: string
    third?: string
    zone?: string
    defensive_actions: number
    share: number
    centroid_x?: number
    centroid_y?: number
  }>
  zone_breakdown?: Array<{
    third?: string
    defensive_actions: number
    share: number
    centroid_x?: number
    centroid_y?: number
  }>
  flank_pressure_gaps?: Array<{
    flank: string
    defensive_actions: number
    share: number
  }>
  gaps?: DefensiveSpacingGap[]
  actions?: DefensiveSpacingAction[]
  notes?: string[]
}
