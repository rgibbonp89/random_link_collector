import React, { useState, useEffect } from 'react';
import logo from './logo.svg';
import './App.css';
import ReactMarkdown from 'react-markdown';
import ReactPaginate from 'react-paginate';


function App() {
  const [jsonData, setJsonData] = useState([]);
  const [page, setPage] = useState(0);
  const [selectedBox, setSelectedBox] = useState(null);


  useEffect(() => {
    // Make an HTTP request to the endpoint and get the JSON data
    fetch('http://127.0.0.1:5000/getallarticles')
      .then(response => response.json())
      .then(data => setJsonData(data))
      .catch(error => console.error(error));
  }, []);

  const handleBoxClick = (boxId) => {
    setSelectedBox(boxId === selectedBox ? null : boxId);
  };


  const itemsPerPage = 10;
  const pageCount = jsonData ? Math.ceil(jsonData.length / itemsPerPage) : 0;
  const offset = page * itemsPerPage;
  const currentPageData = jsonData.slice(offset, offset + itemsPerPage);

  const handlePageClick = (selectedPage) => {
    setPage(selectedPage.selected);
    setSelectedBox(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.js</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
        {currentPageData.map(item => (
          <div key={item.name_input} className={`box ${item.name_input === selectedBox ? 'box--selected' : ''}`} onClick={() => handleBoxClick(item.name_input)}>
            <h2>Article name: {item.name_input}</h2>
            <p>URL: {item.url_input}</p>
            <p className="subheader"> Description:</p>
            <ReactMarkdown>{item.auto_summary}</ReactMarkdown>
            <p className="subheader"> My summary:</p>
            <ReactMarkdown>{item.my_summary}</ReactMarkdown>
          </div>
        ))}
        <ReactPaginate
          pageCount={pageCount}
          onPageChange={handlePageClick}
          containerClassName={'pagination'}
          pageLinkClassName={'page-link'}
          previousLinkClassName={'page-link'}
          nextLinkClassName={'page-link'}
          disabledClassName={'disabled'}
          activeClassName={'active'}
          pageRangeDisplayed={5}
          marginPagesDisplayed={2}
          pageLinkStyle={{ listStyleType: 'none' }}

        />
      </header>
    </div>
  );
}

export default App;
