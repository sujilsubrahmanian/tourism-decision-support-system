import { useState, useEffect } from "react";

function App() {
  const [locations, setLocations] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/locations")
      .then((response) => response.json())
      .then((data) => setLocations(data))
      .catch((error) => console.error("Error fetching locations:", error));
  }, []);

  return (
    <div>
      <h1>Tourism Decision Support System</h1>
      <ul>
        {locations.map((loc) => (
          <li key={loc.id}>
            {loc.name} — {loc.category} ({loc.state})
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;