import React from "react";
import {Link } from "react-router-dom";
import './pages/App.css';

function Navbar() {
  return (
    <nav>
      <ul className={'navbar'}>
        <li>
           <Link to ="/">Home</Link>
        </li>
        <li>
          <Link to="/submit">Submit</Link>
        </li>
      </ul>
    </nav>
  );
}

export default Navbar;
