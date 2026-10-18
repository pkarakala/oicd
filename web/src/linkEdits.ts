// Pure edits of a Link: each sets an input value and returns a new Link. No physics here;
// the edited Link goes to POST /evaluate, which computes everything.

import type { Link, Provenance } from './types'

// An edited value no longer matches its original source, so it is relabeled SYNTHETIC
// (CLAUDE.md rule 1: a value with no source is synthetic).
export const EDITED: Provenance = {
  source_class: 'synthetic',
  citation_key: null,
  rationale: 'Set interactively in the explorer (synthetic what-if value).',
}

const ADDED_CONNECTOR: Provenance = {
  source_class: 'synthetic',
  citation_key: null,
  rationale: 'Connector added in the explorer; 0.5 dB as in model card T05 (synthetic).',
}

const ADDED_CONNECTOR_LOSS_DB = 0.5

export function setLoss(link: Link, index: number, lossDb: number): Link {
  return {
    ...link,
    channel: link.channel.map((element, i) =>
      i === index ? { ...element, loss_max: { value: { value: lossDb }, provenance: EDITED } } : element,
    ),
  }
}

export function setLaunch(link: Link, dbm: number): Link {
  const q = link.tx.launch_oma_min
  return {
    ...link,
    tx: {
      ...link.tx,
      launch_oma_min: { value: { ...q.value, power_dbm: { value: dbm } }, provenance: EDITED },
    },
  }
}

export function setSensitivity(link: Link, dbm: number): Link {
  const q = link.rx.sensitivity_oma_max
  return {
    ...link,
    rx: {
      ...link.rx,
      sensitivity_oma_max: { value: { ...q.value, power_dbm: { value: dbm } }, provenance: EDITED },
    },
  }
}

export function setPenalty(link: Link, index: number, db: number): Link {
  return {
    ...link,
    penalties: link.penalties.map((p, i) =>
      i === index ? { ...p, value: { value: { value: db }, provenance: EDITED } } : p,
    ),
  }
}

export function setReserve(link: Link, db: number): Link {
  return { ...link, reserve: { value: { value: db }, provenance: EDITED } }
}

/** Insert a connector just before the last channel element (the RX FAU mating). */
export function addConnector(link: Link): Link {
  const count = link.channel.filter((e) => e.name.startsWith('added connector')).length
  const connector = {
    name: `added connector ${count + 1}`,
    loss_max: { value: { value: ADDED_CONNECTOR_LOSS_DB }, provenance: ADDED_CONNECTOR },
  }
  const at = Math.max(link.channel.length - 1, 0)
  return { ...link, channel: [...link.channel.slice(0, at), connector, ...link.channel.slice(at)] }
}
