import React, { useEffect, useState } from "react";

export default function ScannerTable() {

  const [data, setData] = useState([]);

  useEffect(() => {

    const fetchScanner = () => {

      fetch("http://localhost:8000/api/radar")
        .then(res => res.json())
        .then(result => setData(result))
        .catch(err => console.error("Scanner fetch error:", err));

    };

    fetchScanner();

    const interval = setInterval(fetchScanner, 5000);

    return () => clearInterval(interval);

  }, []);

  return (

    <div>

      <h3>Market Scanner</h3>

      <table className="scanner-table">

        <thead>
          <tr>
            <th>Instrument</th>
            <th>Score</th>
            <th>Signals</th>
          </tr>
        </thead>

        <tbody>

          {data.length === 0 && (
            <tr>
              <td colSpan="3">No opportunities detected</td>
            </tr>
          )}

          {data.map((row, index) => (

            <tr key={index}>

              <td>{row.instrument}</td>

              <td>{row.score}</td>

              <td>{(row.signals || []).join(", ")}</td>

            </tr>

          ))}

        </tbody>

      </table>

    </div>

  );

}
