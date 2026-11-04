import React, { useState, useEffect, useRef, useCallback } from 'react'
import { motion } from 'framer-motion'
import { MapPin, Phone, Star, Search, ExternalLink, Navigation, Clock, Filter } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'

const TYPE_CONFIG = {
  hospital: { label: 'Hospital',   bg: 'bg-blue-50 dark:bg-blue-900/20',    text: 'text-blue-600 dark:text-blue-400',    pin: '#3b82f6' },
  clinic:   { label: 'Clinic',     bg: 'bg-green-50 dark:bg-green-900/20',  text: 'text-green-600 dark:text-green-400',  pin: '#22c55e' },
  pharmacy: { label: 'Pharmacy',   bg: 'bg-purple-50 dark:bg-purple-900/20',text: 'text-purple-600 dark:text-purple-400',pin: '#a855f7' },
  dental:   { label: 'Dental',     bg: 'bg-teal-50 dark:bg-teal-900/20',    text: 'text-teal-600 dark:text-teal-400',    pin: '#14b8a6' },
}

const GMAP_TYPES = {
  hospital: ['hospital'],
  clinic:   ['doctor'],
  pharmacy: ['pharmacy'],
  dental:   ['dentist'],
}

function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

export default function Hospitals() {
  const { t } = useTranslation()
  const mapRef        = useRef(null)
  const googleMap     = useRef(null)
  const markersRef    = useRef([])
  const infoWindowRef = useRef(null)
  const serviceRef    = useRef(null)

  const [hospitals, setHospitals]     = useState([])
  const [loading, setLoading]         = useState(false)
  const [search, setSearch]           = useState('')
  const [typeFilter, setTypeFilter]   = useState('all')
  const [userPos, setUserPos]         = useState(null)
  const [selected, setSelected]       = useState(null)
  const [mapReady, setMapReady]       = useState(false)
  const [locationDenied, setLocationDenied] = useState(false)

  /* ── Load Google Maps API ─────────────────────────────────────────── */
  useEffect(() => {
    if (window.google?.maps) { setMapReady(true); return }
    // Use free Maps Embed / free JS API without billing key for basic geocoding
    // For full Places API, user must add GOOGLE_MAPS_API_KEY to .env
    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_KEY || ''
    const script = document.createElement('script')
    script.id  = 'google-maps-script'
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&callback=__gmapsInit`
    script.async = true
    script.defer = true
    window.__gmapsInit = () => {
      delete window.__gmapsInit
      setMapReady(true)
    }
    script.onerror = () => {
      console.warn('Google Maps failed to load — API key may be missing or invalid')
      setMapReady(false)
    }
    document.head.appendChild(script)
    return () => { if (window.__gmapsInit) delete window.__gmapsInit }
  }, [])

  /* ── Init map once Google is ready ───────────────────────────────── */
  useEffect(() => {
    if (!mapReady || !mapRef.current || googleMap.current) return
    const G = window.google.maps
    const center = userPos ? { lat: userPos.lat, lng: userPos.lng } : { lat: 20.5937, lng: 78.9629 }
    googleMap.current = new G.Map(mapRef.current, {
      center,
      zoom: userPos ? 14 : 5,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: true,
      zoomControlOptions: { position: G.ControlPosition.RIGHT_CENTER },
      styles: [
        { featureType: 'poi', elementType: 'labels', stylers: [{ visibility: 'off' }] },
        { featureType: 'transit', stylers: [{ visibility: 'off' }] },
      ],
    })
    infoWindowRef.current = new G.InfoWindow()
    serviceRef.current    = new G.places.PlacesService(googleMap.current)
    if (userPos) {
      new G.Marker({
        position: { lat: userPos.lat, lng: userPos.lng },
        map: googleMap.current,
        icon: { path: G.SymbolPath.CIRCLE, scale: 10, fillColor: '#3b82f6', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 2 },
        title: 'Your Location',
        zIndex: 9999,
      })
    }
  }, [mapReady, userPos])

  /* ── Clear + place markers ────────────────────────────────────────── */
  const placeMarkers = useCallback((places) => {
    if (!googleMap.current || !window.google?.maps) return
    const G = window.google.maps
    markersRef.current.forEach(m => m.setMap(null))
    markersRef.current = []
    places.forEach(h => {
      if (!h.lat || !h.lng) return
      const tc = TYPE_CONFIG[h.type] || TYPE_CONFIG.hospital
      const marker = new G.Marker({
        position: { lat: h.lat, lng: h.lng },
        map: googleMap.current,
        title: h.name,
        icon: {
          path: 'M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z',
          fillColor: tc.pin,
          fillOpacity: 1,
          strokeColor: '#fff',
          strokeWeight: 1.5,
          scale: 1.8,
          anchor: new G.Point(12, 22),
        },
      })
      marker.addListener('click', () => {
        setSelected(h)
        googleMap.current.panTo({ lat: h.lat, lng: h.lng })
        const content = `
          <div style="font-family:sans-serif;max-width:220px;padding:4px">
            <b style="font-size:14px">${h.name}</b><br/>
            <span style="color:${tc.pin};font-size:12px">${tc.label}</span><br/>
            ${h.address ? `<span style="font-size:12px;color:#666">${h.address}</span><br/>` : ''}
            ${h.distance_km != null ? `<span style="font-size:12px;color:#3b82f6">${h.distance_km.toFixed(1)} km away</span><br/>` : ''}
            ${h.rating ? `<span style="font-size:12px">⭐ ${h.rating}</span><br/>` : ''}
            ${h.open !== undefined ? `<span style="color:${h.open ? '#22c55e' : '#ef4444'};font-size:12px">${h.open ? 'Open Now' : 'Closed'}</span>` : ''}
          </div>`
        infoWindowRef.current.setContent(content)
        infoWindowRef.current.open(googleMap.current, marker)
      })
      markersRef.current.push(marker)
    })
  }, [])

  /* ── Fetch nearby via Google Places ──────────────────────────────── */
  const fetchNearby = useCallback(async (lat, lng) => {
    if (!serviceRef.current || !window.google?.maps) return
    setLoading(true)
    const G   = window.google.maps
    const loc = new G.LatLng(lat, lng)
    const allResults = []
    const types = typeFilter === 'all'
      ? ['hospital', 'clinic', 'pharmacy', 'dental']
      : [typeFilter]

    const fetchType = (type) => new Promise((resolve) => {
      const gmTypes = GMAP_TYPES[type] || ['hospital']
      serviceRef.current.nearbySearch(
        { location: loc, radius: 8000, type: gmTypes[0] },
        (results, status) => {
          if (status === G.places.PlacesServiceStatus.OK && results) {
            const mapped = results.slice(0, 20).map(r => ({
              id:          r.place_id,
              name:        r.name,
              type,
              address:     r.vicinity,
              lat:         r.geometry.location.lat(),
              lng:         r.geometry.location.lng(),
              rating:      r.rating || null,
              open:        r.opening_hours?.open_now,
              distance_km: haversineKm(lat, lng, r.geometry.location.lat(), r.geometry.location.lng()),
              place_id:    r.place_id,
            }))
            resolve(mapped)
          } else {
            resolve([])
          }
        }
      )
    })

    try {
      const results = await Promise.all(types.map(fetchType))
      const flat = results.flat().sort((a, b) => (a.distance_km || 99) - (b.distance_km || 99))
      setHospitals(flat)
      placeMarkers(flat)
      if (flat.length === 0) toast('No facilities found nearby.', { icon: 'ℹ️' })
    } catch (e) {
      toast.error('Failed to fetch nearby facilities.')
    } finally {
      setLoading(false)
    }
  }, [typeFilter, placeMarkers])

  /* ── Geolocation ──────────────────────────────────────────────────── */
  useEffect(() => {
    if (!navigator.geolocation) { setLocationDenied(true); return }
    navigator.geolocation.getCurrentPosition(
      pos => {
        const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude }
        setUserPos(coords)
      },
      () => setLocationDenied(true),
      { timeout: 10000, maximumAge: 300000 }
    )
  }, [])

  /* ── Fetch when map + position are both ready ─────────────────────── */
  useEffect(() => {
    if (mapReady && userPos && serviceRef.current) {
      fetchNearby(userPos.lat, userPos.lng)
    }
  }, [mapReady, userPos, fetchNearby])

  /* ── Text search ──────────────────────────────────────────────────── */
  const handleSearch = () => {
    if (!search.trim() || !serviceRef.current || !window.google?.maps) {
      toast.error('Enter a search term or allow location access.')
      return
    }
    setLoading(true)
    const G = window.google.maps
    serviceRef.current.textSearch(
      { query: search + ' hospital clinic pharmacy', region: 'in' },
      (results, status) => {
        if (status === G.places.PlacesServiceStatus.OK && results) {
          const mapped = results.slice(0, 30).map(r => ({
            id:          r.place_id,
            name:        r.name,
            type:        r.types?.includes('hospital') ? 'hospital' : r.types?.includes('pharmacy') ? 'pharmacy' : r.types?.includes('dentist') ? 'dental' : 'clinic',
            address:     r.formatted_address || r.vicinity,
            lat:         r.geometry.location.lat(),
            lng:         r.geometry.location.lng(),
            rating:      r.rating || null,
            open:        r.opening_hours?.open_now,
            distance_km: userPos ? haversineKm(userPos.lat, userPos.lng, r.geometry.location.lat(), r.geometry.location.lng()) : null,
            place_id:    r.place_id,
          }))
          setHospitals(mapped)
          placeMarkers(mapped)
          if (mapped[0]) googleMap.current?.panTo({ lat: mapped[0].lat, lng: mapped[0].lng })
          googleMap.current?.setZoom(13)
        } else {
          toast.error('No results found.')
        }
        setLoading(false)
      }
    )
  }

  /* ── Apply type filter to existing results ────────────────────────── */
  const filtered = typeFilter === 'all' ? hospitals : hospitals.filter(h => h.type === typeFilter)

  const TYPE_FILTERS = [
    { key: 'all',      label: 'All Facilities' },
    { key: 'hospital', label: 'Hospitals' },
    { key: 'clinic',   label: 'Clinics' },
    { key: 'pharmacy', label: 'Pharmacies' },
    { key: 'dental',   label: 'Dental Clinics' },
  ]

  const handleSelectHospital = (h) => {
    setSelected(h)
    if (googleMap.current && h.lat) {
      googleMap.current.panTo({ lat: h.lat, lng: h.lng })
      googleMap.current.setZoom(16)
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="section-title">{t('hospitals.title', 'Nearby Healthcare Facilities')}</h1>
        <p className="section-subtitle text-sm">{t('hospitals.subtitle', 'Real-time hospital and clinic data powered by Google Maps')}</p>
      </div>

      {/* Search + Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="Search hospitals, clinics, city..."
            className="input-field pl-10" />
        </div>
        <button onClick={handleSearch} className="btn-primary px-5 flex-shrink-0">
          <Search size={15} /> Search
        </button>
      </div>

      {/* Type Filter Pills */}
      <div className="flex gap-2 flex-wrap">
        {TYPE_FILTERS.map(({ key, label }) => (
          <button key={key} onClick={() => setTypeFilter(key)}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
              typeFilter === key
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-blue-300'
            }`}>
            {label}
          </button>
        ))}
      </div>

      {/* Alerts */}
      {locationDenied && (
        <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl text-sm text-amber-700 dark:text-amber-400">
          <Navigation size={15} /> Location denied. Search by hospital name or city above.
        </div>
      )}
      {!window.google?.maps && mapReady === false && (
        <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-xl text-sm text-blue-700 dark:text-blue-400">
          Add <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">VITE_GOOGLE_MAPS_KEY=your_key</code> to <code>frontend/.env</code> for live Google Maps. Using fallback mode.
        </div>
      )}

      {/* ── Main Layout: Map LEFT + List RIGHT ── */}
      <div className="flex flex-col lg:flex-row gap-4" style={{ minHeight: '560px' }}>

        {/* Google Map */}
        <div className="lg:flex-1 glass-card overflow-hidden rounded-2xl" style={{ minHeight: '400px', position: 'relative' }}>
          <div ref={mapRef} style={{ width: '100%', height: '100%', minHeight: '400px' }} />
          {!mapReady && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-100 dark:bg-slate-800">
              <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-3" />
              <p className="text-slate-400 text-sm">Loading Google Maps...</p>
            </div>
          )}
          {loading && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-white dark:bg-slate-800 shadow-lg rounded-full px-4 py-2 text-sm text-slate-600 dark:text-slate-300 z-10">
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              Finding nearby facilities...
            </div>
          )}
        </div>

        {/* Hospital List */}
        <div className="lg:w-96 flex flex-col gap-2 overflow-y-auto" style={{ maxHeight: '600px' }}>
          {filtered.length === 0 && !loading ? (
            <div className="glass-card p-6 text-center text-slate-400">
              <MapPin size={36} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">
                {hospitals.length === 0
                  ? 'Allow location or search to find hospitals.'
                  : 'No facilities match the selected filter.'}
              </p>
            </div>
          ) : (
            filtered.map((h, i) => {
              const tc = TYPE_CONFIG[h.type] || TYPE_CONFIG.hospital
              const isSelected = selected?.id === h.id
              return (
                <motion.div key={h.id || i}
                  initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03 }}
                  onClick={() => handleSelectHospital(h)}
                  className={`glass-card p-3.5 cursor-pointer transition-all hover:shadow-md ${isSelected ? 'ring-2 ring-blue-500 shadow-md' : ''}`}>

                  <div className="flex items-start gap-3">
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${tc.bg}`}>
                      <MapPin size={16} className={tc.text} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-1">
                        <p className="font-semibold text-slate-800 dark:text-slate-100 text-sm leading-tight truncate">{h.name}</p>
                        {h.distance_km != null && (
                          <span className="text-xs text-blue-600 dark:text-blue-400 font-medium flex-shrink-0 ml-1">
                            {h.distance_km.toFixed(1)}km
                          </span>
                        )}
                      </div>
                      <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${tc.bg} ${tc.text}`}>{tc.label}</span>
                      {h.address && <p className="text-xs text-slate-400 mt-1 truncate">{h.address}</p>}
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        {h.rating && (
                          <span className="flex items-center gap-0.5 text-xs text-amber-500">
                            <Star size={11} className="fill-amber-400" /> {h.rating}
                          </span>
                        )}
                        {h.open !== undefined && (
                          <span className={`text-xs font-medium ${h.open ? 'text-green-600' : 'text-red-500'}`}>
                            {h.open ? 'Open' : 'Closed'}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {isSelected && (
                    <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700 flex gap-2">
                      <a href={`https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lng}`}
                        target="_blank" rel="noopener noreferrer"
                        onClick={e => e.stopPropagation()}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 bg-blue-600 text-white rounded-xl text-xs font-medium hover:bg-blue-700 transition-colors">
                        <Navigation size={12} /> Directions
                      </a>
                      <a href={`https://www.google.com/maps/place/?q=place_id:${h.place_id || ''}`}
                        target="_blank" rel="noopener noreferrer"
                        onClick={e => e.stopPropagation()}
                        className="flex items-center justify-center gap-1.5 px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-500 hover:text-blue-500 hover:border-blue-300 transition-colors">
                        <ExternalLink size={12} /> Details
                      </a>
                    </div>
                  )}
                </motion.div>
              )
            })
          )}
        </div>
      </div>

      <p className="text-xs text-center text-slate-400">
        Powered by Google Maps Places API. Results show real healthcare facilities near your location.
      </p>
    </div>
  )
}
