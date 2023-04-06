import ReactDOM from "react-dom";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./Layout";
import Home from "./pages/Home";
import Submit from "./pages/Submit";
import Syntheses from "./pages/Syntheses";
import DailyNotes from "./pages/DailyNotes";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="submit" element={<Submit />} />
          <Route path="syntheses" element={<Syntheses />} />
          <Route path="dailynotes" element={<DailyNotes />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

ReactDOM.render(<App />, document.getElementById("root"));
