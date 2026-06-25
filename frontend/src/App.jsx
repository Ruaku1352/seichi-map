import { useEffect, useState } from 'react'
import { APIProvider, Map, Marker } from '@vis.gl/react-google-maps'

const TOKYO = { lat: 35.6762, lng: 139.6503 }

function Card({ spot, onClose }) {
  return (
    <div style={{
      position: 'absolute', bottom: 32, left: '50%', transform: 'translateX(-50%)',
      background: 'white', borderRadius: 12, padding: '16px 20px', width: 320,
      boxShadow: '0 4px 16px rgba(0,0,0,0.2)', zIndex: 10,
    }}>
      <button onClick={onClose} style={{
        position: 'absolute', top: 8, right: 12,
        background: 'none', border: 'none', fontSize: 18, cursor: 'pointer',
      }}>✕</button>
      <div style={{ fontSize: 13, color: '#888', marginBottom: 4 }}>{spot.anime_title_ja}</div>
      <div style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 8 }}>{spot.spot_name_ja}</div>
      <div style={{ fontSize: 14, color: '#444', lineHeight: 1.6 }}>{spot.intro_short_en}</div>
    </div>
  )
}

function App() {
  const [spots, setSpots] = useState([])
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    fetch('/seichi_data.json')
      .then(r => r.json())
      .then(setSpots)
  }, [])

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh' }}>
      <APIProvider apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY}>
        <Map
          style={{ width: '100%', height: '100%' }}
          defaultCenter={TOKYO}
          defaultZoom={14}
          gestureHandling="greedy"
          disableDefaultUI={false}
          onClick={() => setSelected(null)}
        >
          {spots.map(spot => (
            <Marker
              key={spot.id}
              position={{ lat: spot.lat, lng: spot.lng }}
              title={spot.spot_name_en}
              onClick={() => setSelected(spot)}
            />
          ))}
        </Map>
      </APIProvider>
      {selected && <Card spot={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}

export default App
