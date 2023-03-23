import React, { useEffect, useState } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";
import ReactPaginate from "react-paginate";

function Syntheses() {
  const [jsonData, setJsonData] = useState([]);
  const [page, setPage] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [cardsPerRow, setCardsPerRow] = useState(2);

  const fetchData = () => {
    const queryParams = `?timestamp=${new Date().getTime()}`;
    fetch(`/getallsyntheses${queryParams}`)
      .then((response) => response.json())
      .then((data) => {
        setJsonData(data);
      })
      .catch((error) => console.error(error));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const itemsPerPage = 10;
  const offset = page * itemsPerPage;
  const filteredData = jsonData.filter((item) => {
    return (
      item.synthesis_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.synthesis.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });
  const pageCount = filteredData
    ? Math.ceil(filteredData.length / itemsPerPage)
    : 0;
  const currentPageData = filteredData.slice(offset, offset + itemsPerPage);
  const numRows = Math.ceil(currentPageData.length / cardsPerRow);

  const handleCardsPerRowChange = (event) => {
    setCardsPerRow(parseInt(event.target.value));
  };
  const handlePageClick = (selectedPage) => {
    setPage(selectedPage.selected);
  };

  return (
    <div className="App" style={{ paddingBottom: "60px" }}>
      <header className="App">
        <input
          className={"search-bar"}
          type="text"
          placeholder="Search syntheses..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </header>
      <div></div>
      {[...Array(numRows)].map((_, rowIndex) => {
        return (
          <div className="App-content">
            {currentPageData
              .slice(rowIndex * cardsPerRow, (rowIndex + 1) * cardsPerRow)
              .map((item) => (
                <div
                  style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    paddingTop: "60px",
                  }}
                >
                  <div className={"box"} key={item.id}>
                    <h2>{item.synthesis_title}</h2>
                    <p className="subheader"> Synthesis:</p>
                    <ReactMarkdown>{item.synthesis}</ReactMarkdown>
                    {item.url_list.map((url, index) => (
                      <div key={index}>
                        <a href={url} target="_blank" rel="noopener noreferrer">
                          {item.name_list[index]}
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        );
      })}
      <ReactPaginate
        pageCount={pageCount}
        onPageChange={handlePageClick}
        containerClassName={"pagination"}
        pageLinkClassName={"page-link"}
        previousLinkClassName={"page-link"}
        nextLinkClassName={"page-link"}
        disabledClassName={"disabled"}
        activeClassName={"active"}
        pageRangeDisplayed={5}
        marginPagesDisplayed={2}
        pageLinkStyle={{ listStyleType: "none" }}
      />
    </div>
  );
}
export default Syntheses;
