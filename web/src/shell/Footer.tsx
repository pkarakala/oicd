import { useCatalog } from '../api/hooks'
import { INDEPENDENCE } from './ui'

/** The brief 03 caption next to the independence line (from the API when it has answered). */
export function Footer() {
  const catalog = useCatalog()
  return (
    <footer className="footer">
      <span data-testid="caption">
        Schematic, not to scale. Values synthetic unless cited. PASS means not excluded by modeled constraints.
      </span>
      <span className="footer-sep" aria-hidden>
        ·
      </span>
      <span data-testid="independence">{catalog.data?.independence ?? INDEPENDENCE}</span>
    </footer>
  )
}
