import React, { useState, useEffect } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";
import ReactPaginate from "react-paginate";

function Home() {
  const [jsonData, setJsonData] = useState([]);
  const [page, setPage] = useState(0);
  const [minimizedBoxes, setMinimizedBoxes] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [readStatusFilter, setReadStatusFilter] = useState("all");
  const [editArticle, setEditArticle] = useState([]);

  const fetchData = () => {
    const queryParams = `?timestamp=${new Date().getTime()}`;
    fetch(`/getallarticles${queryParams}`)
      .then((response) => response.json())
      .then((data) => {
        setJsonData(data);
        setMinimizedBoxes(data.map((item) => item.name_input));
      })
      .catch((error) => console.error(error));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const labelVisualizationEnum = {
    "www.phenomenalworld.org": "Phenomenal World",
    "www.ft.com": "FT",
    "open.substack.com": "Substack",
    "substack.com": "Substack",
    "www.foreignaffairs.com": "Foreign Affairs",
    "www.currentaffairs.org": "Current Affairs",
  };

  function fuzzyMatchEnum(key) {
    for (const enumKey in labelVisualizationEnum) {
      if (key.includes(enumKey)) {
        return labelVisualizationEnum[enumKey];
      }
    }
    return key;
  }

  const handleBoxMinimize = (boxId) => {
    if (!minimizedBoxes.includes(boxId)) {
      setMinimizedBoxes([...minimizedBoxes, boxId]);
    } else {
      setMinimizedBoxes(minimizedBoxes.filter((id) => id !== boxId));
    }
  };

  const itemsPerPage = 10;
  const offset = page * itemsPerPage;

  const filteredData = jsonData.filter((item) => {
    const includesSearchQuery = item.name_input
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    if (readStatusFilter === "all") {
      return includesSearchQuery;
    } else if (readStatusFilter === "read") {
      return item.read_status && includesSearchQuery;
    } else if (readStatusFilter === "unread") {
      return !item.read_status && includesSearchQuery;
    }
    return true; // fallback for invalid readStatusFilter values
  });
  const pageCount = filteredData
    ? Math.ceil(filteredData.length / itemsPerPage)
    : 0;
  const currentPageData = filteredData.slice(offset, offset + itemsPerPage);

  const handlePageClick = (selectedPage) => {
    setPage(selectedPage.selected);
  };

  const handleToggleRead = (item) => {
    const newStatus = !item.read_status; // flip the read status
    fetch(`/update_article`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: item.id, read_status: newStatus }),
    })
      .then((response) => response.json())
      .then((data) => {
        setJsonData((prevData) =>
          prevData.map((d) =>
            d.id === item.id ? { ...d, read_status: newStatus } : d
          )
        );
      });
  };

  const handleDeleteArticle = (item) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this article?"
    );
    if (confirmed) {
      fetch(`/deletearticle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: item.id }),
      })
        .then(() => {
          setJsonData(jsonData.filter((d) => d.id !== item.id));
        })
        .catch((error) => console.error(error));
    } else {
      const handleCancelDelete = () => {};
    }
  };

  const handleEditArticle = (event, item) => {
    event.preventDefault();
    const updatedArticle = {
      id: item.id,
      name_input: event.target.elements.articleName.value,
      site_label: event.target.elements.articleSite.value,
      auto_summary: event.target.elements.articleAutoSummary.value,
      my_summary: event.target.elements.articleMySummary.value,
    };
    fetch(`/update_article`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updatedArticle),
    })
      .then((response) => response.json())
      .then((data) => {
        setJsonData((prevData) =>
          prevData.map((d) =>
            d.id === item.id ? { ...d, ...updatedArticle } : d
          )
        );
      });
  };

  return (
    <div className="App">
      <header className="App-header">
        <p>Welcome to the article saver!</p>
      </header>
      <header className="App"></header>
      <input
        className={"search-bar"}
        type="text"
        placeholder="Search articles..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />
      <div style={{ display: "flex", justifyContent: "flex-start" }}>
        <button
          onClick={() => setReadStatusFilter("all")}
          className={`button ${readStatusFilter === "all" ? "active" : ""}`}
        >
          All
        </button>
        <button
          onClick={() => setReadStatusFilter("read")}
          className={`button ${readStatusFilter === "read" ? "active" : ""}`}
        >
          Read
        </button>
        <button
          onClick={() => setReadStatusFilter("unread")}
          className={`button ${readStatusFilter === "unread" ? "active" : ""}`}
        >
          Unread
        </button>
      </div>
      {currentPageData.map((item) => (
        <div
          key={item.name_input}
          className={`box
               ${
                 minimizedBoxes.includes(item.name_input)
                   ? "box--minimized"
                   : ""
               }`}
        >
          <div className="tag">{fuzzyMatchEnum(item.site_label)}</div>
          <a href={item.url_input}>
            <h2>{item.name_input}</h2>
          </a>
          <p>Short summary: {item.short_summary}</p>
          <button
            className={"button"}
            onClick={() => handleBoxMinimize(item.name_input)}
          >
            Expand
          </button>
          <button className={"button"} onClick={() => handleToggleRead(item)}>
            {item.read_status ? "Read" : "Unread"}
          </button>
          <button
            className={"button delete-btn"}
            onClick={() => handleDeleteArticle(item)}
          >
            Delete
          </button>

          {editArticle !== item && (
            <button
              className={"button"}
              onClick={() => setEditArticle(item)}
              style={{
                display: minimizedBoxes.includes(item.name_input)
                  ? "none"
                  : "block",
              }}
            >
              Edit
            </button>
          )}
          {editArticle === item && (
            <form onSubmit={(event) => handleEditArticle(event, item)}>
              <input
                className={"input"}
                type="text"
                name="articleName"
                defaultValue={item.name_input}
                style={{ padding: "10px", marginBottom: "10px" }}
              />
              <input
                className={"input"}
                type="text"
                name="articleSite"
                defaultValue={item.site_label}
                style={{ padding: "10px", marginBottom: "10px" }}
              />
              <textarea
                className={"textarea"}
                type="text"
                name="articleAutoSummary"
                defaultValue={item.auto_summary}
                style={{ padding: "10px", marginBottom: "10px" }}
              />
              <textarea
                className={"textarea"}
                type="text"
                name="articleMySummary"
                defaultValue={item.my_summary}
                style={{ padding: "10px", marginBottom: "10px" }}
              />
              <button type="submit">Save</button>
            </form>
          )}
          {!minimizedBoxes.includes(item.name_input) && (
            <>
              <p className="subheader"> Auto-summary:</p>
              <ReactMarkdown>{item.auto_summary}</ReactMarkdown>
              <p className="subheader"> My summary:</p>
              <ReactMarkdown>{item.my_summary}</ReactMarkdown>
            </>
          )}
        </div>
      ))}
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

export default Home;
