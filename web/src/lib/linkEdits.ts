// Pure edits of a Link: each sets an input value and returns a new Link. No physics here; the
// edited Link goes to the API, which computes everything.

import type { Link, Provenance } from '../api/client'

// An edited value no longer matches its original source, so it is relabeled SYNTHETIC
// (a value with no source is synthetic).
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
      i === index
        ? {
            ...element,
            loss_max: { value: { value: lossDb }, provenance: EDITED },
            // a distribution keeps its sigma and follows the new nominal loss
            loss_distribution: element.loss_distribution
              ? { ...element.loss_distribution, mean: { value: { value: lossDb }, provenance: EDITED } }
              : element.loss_distribution,
          }
        : element,
    ),
  }
}

export function setLaunch(link: Link, dbm: number): Link {
  const q = link.tx.launch_oma_min
  if (q === null || q === undefined) return link
  return {
    ...link,
    tx: { ...link.tx, launch_oma_min: { value: { ...q.value, power_dbm: { value: dbm } }, provenance: EDITED } },
  }
}

export function setSensitivity(link: Link, dbm: number): Link {
  const q = link.rx.sensitivity_oma_max
  return {
    ...link,
    rx: { ...link.rx, sensitivity_oma_max: { value: { ...q.value, power_dbm: { value: dbm } }, provenance: EDITED } },
  }
}

export function setPenalty(link: Link, index: number, db: number): Link {
  return {
    ...link,
    penalties: link.penalties.map((p, i) => (i === index ? { ...p, value: { value: { value: db }, provenance: EDITED } } : p)),
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

/** The 1:N split of an upstream chain (model card §10); unchanged without a chain. */
export function setSplit(link: Link, n: number): Link {
  const chain = link.tx.upstream
  if (chain === null || chain === undefined) return link
  return { ...link, tx: { ...link.tx, upstream: { ...chain, split_n: { value: n, provenance: EDITED } } } }
}

/** A normal loss distribution with sigma (dB) on a channel element (model card §11); 0 removes it. */
export function setSigma(link: Link, index: number, sigmaDb: number): Link {
  return {
    ...link,
    channel: link.channel.map((element, i) => {
      if (i !== index) return element
      if (sigmaDb <= 0) return { ...element, loss_distribution: null }
      return {
        ...element,
        loss_distribution: {
          mean: element.loss_distribution?.mean ?? { value: element.loss_max.value, provenance: EDITED },
          sigma: { value: { value: sigmaDb }, provenance: EDITED },
        },
      }
    }),
  }
}

/** Set a sweepable input by its engine path (model card §8), for loading a swept design. */
export function setPath(link: Link, path: string, value: number): Link {
  const loss = /^channel\[(\d+)\]\.loss_max$/.exec(path)
  if (loss) return setLoss(link, Number(loss[1]), value)
  const penalty = /^penalties\[(\d+)\]\.value$/.exec(path)
  if (penalty) return setPenalty(link, Number(penalty[1]), value)
  if (path === 'reserve') return setReserve(link, value)
  if (path === 'tx.launch_oma_min') return setLaunch(link, value)
  if (path === 'rx.sensitivity_oma_max') return setSensitivity(link, value)
  return link
}

/** Current value of a sweepable input, read from the Link (display only). */
export function pathValue(link: Link, path: string): number | null {
  const loss = /^channel\[(\d+)\]\.loss_max$/.exec(path)
  if (loss) return link.channel[Number(loss[1])]?.loss_max.value.value ?? null
  const penalty = /^penalties\[(\d+)\]\.value$/.exec(path)
  if (penalty) return link.penalties[Number(penalty[1])]?.value.value.value ?? null
  if (path === 'reserve') return link.reserve.value.value
  if (path === 'tx.launch_oma_min') return link.tx.launch_oma_min?.value.power_dbm.value ?? null
  if (path === 'rx.sensitivity_oma_max') return link.rx.sensitivity_oma_max.value.power_dbm.value
  return null
}
