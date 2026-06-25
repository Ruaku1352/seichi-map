import { useEffect, useState } from 'react'
import { APIProvider, Map, Marker } from '@vis.gl/react-google-maps'

const TOKYO = { lat: 35.6762, lng: 139.6503 }

function App() {
  const [spots, setSpots] = useState([])

  useEffect(() => {
    fetch('/seichi_data.json')
      .then(r => r.json())
      .then(setSpots)
  }, [])

  return (
    <APIProvider apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY}>
      <Map
        style={{ width: '100vw', height: '100vh' }}
        defaultCenter={TOKYO}
        defaultZoom={14}
        gestureHandling="greedy"
        disableDefaultUI={false}
      >
        {spots.map(spot => (
          <Marker
            key={spot.id}
            position={{ lat: spot.lat, lng: spot.lng }}
            title={spot.spot_name_en}
          />
        ))}
      </Map>
    </APIProvider>
  )
}

export default App
