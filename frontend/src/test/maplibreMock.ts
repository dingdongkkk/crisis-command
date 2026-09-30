/**
 * jsdom has no WebGL, so unit tests replace maplibre-gl with this recorder. It keeps the
 * public surface MapView uses; real rendering is verified in a browser (screenshots).
 */
type Handler = (...args: unknown[]) => void

export const created: { options: Record<string, unknown>; controls: unknown[]; styles: unknown[] }[] = []
export const instances: Map[] = []

export class Map {
  private handlers: Record<string, Handler[]> = {}
  private sources: Record<string, { setData: (d: unknown) => void; data: unknown }> = {}
  private layers = new Set<string>()
  readonly record: (typeof created)[number]
  readonly container: HTMLElement
  /** MapLibre reports false while any tile or source is still loading. */
  styleLoaded = true

  constructor(options: Record<string, unknown>) {
    this.container = options.container as HTMLElement
    this.record = { options, controls: [], styles: [options.style] }
    created.push(this.record)
    instances.push(this)
    setTimeout(() => this.fire('style.load'))
  }
  on(event: string, fn: Handler) {
    ;(this.handlers[event] ??= []).push(fn)
    return this
  }
  fire(event: string) {
    for (const fn of this.handlers[event] ?? []) fn({})
  }
  addControl(control: unknown) {
    this.record.controls.push(control)
    return this
  }
  addSource(id: string, source: { data: unknown }) {
    const entry = { data: source.data, setData: (d: unknown) => (entry.data = d) }
    this.sources[id] = entry
  }
  getSource(id: string) {
    return this.sources[id]
  }
  sourceData(id: string) {
    return this.sources[id]?.data
  }
  addLayer(layer: { id: string }) {
    this.layers.add(layer.id)
  }
  getLayer(id: string) {
    return this.layers.has(id) ? { id } : undefined
  }
  setPaintProperty() {}
  isStyleLoaded() {
    return this.styleLoaded
  }
  setStyle(style: unknown) {
    this.record.styles.push(style)
    this.layers.clear()
    this.sources = {}
    setTimeout(() => this.fire('style.load'))
  }
  fitBounds() {}
  easeTo() {}
  resize() {}
  getZoom() {
    return 12
  }
  getCenter() {
    return { lng: 77.62, lat: 12.96 }
  }
  getBearing() {
    return -12
  }
  getPitch() {
    return 42
  }
  remove() {}
}

export class Marker {
  private element: HTMLElement
  constructor(options: { element: HTMLElement }) {
    this.element = options.element
  }
  setLngLat() {
    return this
  }
  addTo(map: Map) {
    map.container.appendChild(this.element)
    return this
  }
  getElement() {
    return this.element
  }
  remove() {
    this.element.remove()
  }
}

export class AttributionControl {
  constructor(readonly options: unknown) {}
}
export class NavigationControl {
  constructor(readonly options: unknown) {}
}
export class LngLatBounds {
  extend() {
    return this
  }
}
export function setWorkerUrl() {}
