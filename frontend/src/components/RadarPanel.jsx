import React, { useEffect, useState } from "react";

export default function RadarPanel() {

  const [signals, setSignals] = useState([]);

  useEffect(() => {

    const fetchRadar = () => {

      fetch("http://localhost:8000/api/radar")
        .then(res => res.json())
        .then(data => setSignals(data))
        .catch(err => console.error("Radar fetch error:", err));

    };

    fetchRadar();

    const interval = setInterval(fetchRadar, 5000);

    return () => clearInterval(interval);

  }, []);

  return (

    <div>

      <h3>Liquidity Radar</h3>

      {signals.length === 0 && (
        <div>No signals detected</div>
      )}

      {signals.map((signal, index) => (

        <div key={index} className="radar-item">

          <div className="radar-symbol">
            {signal.instrument}
          </div>

          <div className="radar-score">
            Score: {signal.score}
          </div>

          <div className="radar-signals">
            {signal.signals.join(", ")}
          </div>

        </div>

      ))}

    </div>

  );

}
