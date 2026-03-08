import React, { useEffect, useState } from "react";

export default function Navbar() {

  const [backendStatus, setBackendStatus] = useState("checking");

  useEffect(() => {

    fetch("http://localhost:8000")
      .then(res => res.json())
      .then(() => setBackendStatus("connected"))
      .catch(() => setBackendStatus("offline"));

  }, []);

  return (

    <div className="navbar">

      <div className="navbar-title">
        Institutional Trading Dashboard
      </div>

      <div className="navbar-status">

        Backend: 
        <span className={`status ${backendStatus}`}>
          {backendStatus}
        </span>

      </div>

    </div>

  );

}
