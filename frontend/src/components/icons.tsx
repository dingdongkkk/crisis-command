import { Ambulance, Building2, Car, CircleHelp, Flame, HeartPulse, Ship, Siren, Truck, Waves, Wind } from 'lucide-react'

interface IconProps {
  size?: number
  strokeWidth?: number
}

/** Display-only icon for an incident kind; it never affects priority. */
export function IncidentKindIcon({ kind, ...props }: IconProps & { kind: string }) {
  if (/collapse|building|structural/.test(kind)) return <Building2 {...props} />
  if (/flood|water|strand/.test(kind)) return <Waves {...props} />
  if (/gas|leak/.test(kind)) return <Wind {...props} />
  if (/fire|smoke/.test(kind)) return <Flame {...props} />
  if (/road|accident|vehicle|crash/.test(kind)) return <Car {...props} />
  if (/cardiac|medical|chest|breath/.test(kind)) return <HeartPulse {...props} />
  return <Siren {...props} />
}

export function UnitTypeIcon({ type, ...props }: IconProps & { type: string }) {
  switch (type) {
    case 'als':
    case 'bls':
      return <Ambulance {...props} />
    case 'fire':
      return <Flame {...props} />
    case 'boat':
      return <Ship {...props} />
    case 'tow':
      return <Truck {...props} />
    default:
      return <CircleHelp {...props} />
  }
}
