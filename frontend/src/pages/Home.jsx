import React, { useState, useEffect } from 'react';
import './App.css';
import ReactMarkdown from 'react-markdown';
import ReactPaginate from 'react-paginate';



function Home() {
  const [jsonData, setJsonData] = useState([]);
  const [page, setPage] = useState(0);
  const [minimizedBoxes, setMinimizedBoxes] = useState([]);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    // Make an HTTP request to the endpoint and get the JSON data
    fetch('http://127.0.0.1:5000/getallarticles')
      .then(response => response.json())
      .then(data => {
        setJsonData(data);
        setMinimizedBoxes(data.map(item => item.name_input));
      })
      .catch(error => console.error(error));
  }, []);


  const handleBoxMinimize = (boxId) => {
    if (!minimizedBoxes.includes(boxId)) {
      setMinimizedBoxes([...minimizedBoxes, boxId]);
    } else {
      setMinimizedBoxes(minimizedBoxes.filter(id => id !== boxId));
    }
  }

  const itemsPerPage = 10;
  const pageCount = jsonData ? Math.ceil(jsonData.length / itemsPerPage) : 0;
  const offset = page * itemsPerPage;
  const currentPageData = jsonData.slice(offset, offset + itemsPerPage);

  const handlePageClick = (selectedPage) => {
    setPage(selectedPage.selected);
  };

  const handleMenuToggle = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <div className="App">

      <header className="App-header">
        <p>
          Welcome to the article saver!
        </p>
      </header>
        <header className="App"></header>

        {currentPageData.map(item => (
          <div key={item.name_input}
               className={`box
               ${minimizedBoxes.includes(item.name_input) ? 'box--minimized' : ''}`}
          >
           <a
               href={item.url_input}>
              <h2>{item.name_input}</h2>
            </a>
            <p>Short summary: {item.short_summary}</p>
            <button className={'button'} onClick={() => handleBoxMinimize(item.name_input)}
            >Expand</button>
            {!minimizedBoxes.includes(item.name_input) &&
              <>
                <p className="subheader"> Auto-summary:</p>
                <ReactMarkdown>{item.auto_summary}</ReactMarkdown>
                <p className="subheader"> My summary:</p>
                <ReactMarkdown>{item.my_summary}</ReactMarkdown>
              </>
            }
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
    </div>
  );
}

export default Home;
