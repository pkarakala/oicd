import { describe, expect, it } from 'vitest'
import type { Link } from '../api/client'
import { addConnector, pathValue, setLoss, setPath, setSigma, setSplit } from './linkEdits'

const q = (value: number) => ({ value: { value }, provenance: { source_class: 'synthetic' as const, citation_key: null, rationale: 'test' } })
const link = {
  name: 't',
  tx: { name: 'tx', launch_oma_min: { value: { power_dbm: { value: 0 }, kind: 'oma' }, provenance: q(0).provenance } },
  rx: { name: 'rx', sensitivity_oma_max: { value: { power_dbm: { value: -6 }, kind: 'oma' }, provenance: q(0).provenance } },
  channel: [
    { name: 'TX FAU mating', loss_max: q(1.5) },
    { name: 'patch connector', loss_max: q(1.0) },
    { name: 'RX FAU mating', loss_max: q(1.5) },
  ],
  penalties: [],
  reserve: q(1.5),
} as unknown as Link

describe('link edits', () => {
  it('relabels an edited value as synthetic', () => {
    const edited = setLoss(link, 1, 2)
    expect(edited.channel[1]?.loss_max.value.value).toBe(2)
    expect(edited.channel[1]?.loss_max.provenance.rationale).toMatch(/what-if/)
    expect(link.channel[1]?.loss_max.value.value).toBe(1) // inputs are never mutated
  })

  it('sets and reads sweep paths', () => {
    const edited = setPath(setPath(link, 'channel[1].loss_max', 1.75), 'tx.launch_oma_min', 0.5)
    expect(pathValue(edited, 'channel[1].loss_max')).toBe(1.75)
    expect(pathValue(edited, 'tx.launch_oma_min')).toBe(0.5)
    expect(setPath(link, 'nowhere', 1)).toBe(link)
  })

  it('adds a connector before the RX mating', () => {
    expect(addConnector(link).channel.map((e) => e.name)).toEqual(['TX FAU mating', 'patch connector', 'added connector 1', 'RX FAU mating'])
  })

  it('sets and clears a loss distribution', () => {
    const withSigma = setSigma(link, 0, 0.2)
    expect(withSigma.channel[0]?.loss_distribution?.sigma.value.value).toBe(0.2)
    expect(withSigma.channel[0]?.loss_distribution?.mean.value.value).toBe(1.5)
    expect(setSigma(withSigma, 0, 0).channel[0]?.loss_distribution).toBeNull()
  })

  it('leaves a link without an upstream chain unchanged by a split edit', () => {
    expect(setSplit(link, 18)).toBe(link)
  })
})
