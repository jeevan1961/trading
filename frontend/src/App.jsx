import React from "react";

import ChartPanel from "./components/ChartPanel.jsx";
import RadarPanel from "./components/RadarPanel.jsx";
import ScannerTable from "./components/ScannerTable.jsx";
import Navbar from "./components/Navbar.jsx";

export default function App() {

  return (

    <div className="app-container">

      <Navbar />

      <div className="dashboard-grid">

        <div className="chart-section">
          <ChartPanel />
        </div>

        <div className="radar-section">
          <RadarPanel />
        </div>

      </div>

      <div className="scanner-section">
        <ScannerTable />
      </div>

    </div>

  );

}
