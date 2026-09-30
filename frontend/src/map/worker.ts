/**
 * MapLibre 6 locates its ES-module worker relative to its own file, which breaks once a
 * bundler relocates the library. `?worker&url` makes Vite bundle the worker (and the shared
 * chunk it imports) into one self-contained file for dev and production alike.
 */
import { setWorkerUrl } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'

setWorkerUrl(workerUrl)
