import type {
  DefensiveSpacingData,
  PassingNetworkData,
  PassingNetworkEdge,
  PassingNetworkNode,
} from '../types'

export type PassingNetworkLayoutNode = PassingNetworkNode & {
  x: number
  y: number
  radius: number
  isCentral: boolean
}

export type PassingNetworkLayoutEdge = PassingNetworkEdge & {
  x1: number
  y1: number
  x2: number
  y2: number
  width: number
}

export type DefensiveSpacingHeatCell = {
  x: number
  y: number
  width: number
  height: number
  count: number
  opacity: number
}

export type DefensiveSpacingLayout = {
  summary: string
  centroid: {
    x: number
    y: number
  }
  compactness: number
  lineStretch: number
  teamBreakdown: DefensiveSpacingData['team_breakdown']
  flankBreakdown: NonNullable<DefensiveSpacingData['flank_breakdown']>
  zoneBreakdown: NonNullable<DefensiveSpacingData['zone_breakdown']>
  flankPressureGaps: NonNullable<DefensiveSpacingData['flank_pressure_gaps']>
  totalActions: number
  heatmap: DefensiveSpacingHeatCell[]
  hotZones: Array<{
    x: number
    y: number
    width: number
    height: number
    count: number
  }>
}

export function formatSpacingZone(cell: { x: number; y: number; width: number; height: number }) {
  const xStart = Math.round(cell.x)
  const xEnd = Math.round(cell.x + cell.width)
  const yStart = Math.round(cell.y)
  const yEnd = Math.round(cell.y + cell.height)
  return `Zone ${xStart}-${xEnd} / ${yStart}-${yEnd}`
}

export function formatPlayerLastName(fullName: string) {
  const trimmed = fullName.trim()
  if (!trimmed) {
    return ''
  }

  const parts = trimmed.split(/\s+/)
  return parts[parts.length - 1]
}

export function buildPassingNetworkLayout(network: PassingNetworkData | undefined | null) {
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

export function buildDefensiveSpacingLayout(data: DefensiveSpacingData | undefined | null) {
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

  const hotZones = [...heatmap].sort((left, right) => right.count - left.count).slice(0, 3)

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
    flankBreakdown: data.flank_breakdown ?? [],
    zoneBreakdown: data.zone_breakdown ?? [],
    flankPressureGaps: data.flank_pressure_gaps ?? [],
    totalActions: maxActions,
    heatmap,
    hotZones,
  }
}
